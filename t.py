from pypbc import Element,Parameters,Pairing,G1,Zr,G2,GT,set_point_format_uncompressed
import random
from hashlib import sha256
from Crypto.Util.number import long_to_bytes
from tree import Node,build,get_leaves,find_path
import warnings
# 忽略 DeprecationWarning 警告
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pickle
params_A = """type a
q 8780710799663312522437781984754049815806883199414208211028653399266475630880222957078625179422662221423155858769582317459277713367317481324925129998224791
h 12016012264891146079388821366740534204802954401251311822919615131047207289359704531102844802183906537786776
r 730750818665451621361119245571504901405976559617
exp2 159
exp1 107
sign1 1
sign0 1
"""
q = 8780710799663312522437781984754049815806883199414208211028653399266475630880222957078625179422662221423155858769582317459277713367317481324925129998224791
r = 730750818665451621361119245571504901405976559617
#q是椭圆曲线上有限域的大小，r是基点的阶
params = Parameters(param_string = params_A)


#print(params)
pairing = Pairing(params)
randomness = Element(pairing,Zr,value = 114514)
def Setup(qbits=512,rbits=160):
    """
    初始化,返回(PK,MK)
    """
    params = Parameters(param_string = params_A)
    pairing = Pairing(params)
    g = Element(pairing,G1,value = "036DC0C7A1738F172135AA08CC9BB22E87BB04D853D24A89CE280A29133BA80D3D85F5648D1A89C7F72DCC60BC1D203F3F58C5E8771506B15200A5FC21270C9CEC")
    alpha = Element.random(pairing,Zr)
    beta = Element.random(pairing,Zr)
    alpha = Element(pairing,Zr,value = 0x01EF)
    beta = Element(pairing,Zr,value = 0x02D5)

    h = g**beta  
    f = g**(~beta)#f=g^1/beta

    root = pairing.apply(g,g)**alpha#e(g,g)^alpha

    PK=(pairing,g,h,f,root)
    MK=(beta,alpha)
    return PK,MK
def choose_poly(PK,T:Node,qr0 = Element.zero(pairing,Zr)):
    (pairing,g,h,f,root) = PK
    CList = dict()
    CList_ = dict()
    if qr0 == Element.zero(pairing,Zr):#选一个qr0，即多项式的f(0)
        qr0 = Element.random(pairing,Zr)

    if T.leave == True:#是叶节点
        return {T.value:g**qr0},{T.value:Element.from_hash(pairing,G1,T.value)**qr0}#Cy,Cy'
    else:
        if T.gate == "and":
            T.kx = len(T.children_nodes)#threshold
        else:
            T.kx = 1
        #coe = [Element.random(pairing,Zr) for _ in range(T.kx-1)]#多项式的系数
        coe = [qr0,Element(pairing,Zr,value = 3)]
        #print("coe:",coe)
        def f(x,coe=coe):
            result = Element.zero(pairing,Zr)
            for i in range(len(coe)):
                result += coe[i] * pow(x,i)
            return result
        for i in range(0,len(T.children_nodes)):
            #print(choose_poly(PK,T.children_nodes[i],qr0=f(i+1)))
            Cy,Cy_ = choose_poly(PK,T.children_nodes[i],qr0=f(i+1))
            CList.update(Cy)
            CList_.update(Cy_)
    return CList,CList_

def Encrypt(PK,M,T:Node):
    (pairing,g,h,f,root) = PK
    #M = Element.from_hash(pairing,GT,"1")
    #s = random.randint(1,r-1)
    s = Element(pairing,Zr,value = 0x0047)
    #s = Element.random(pairing,Zr)
    C_Main = M+(root**s)#*M #pow(root,s) * M#主密文
    #print("root^s:",root**s)
    C = h ** s
    CList,CList_=choose_poly(PK,T,s)

    CT = (T,C_Main,C,CList,CList_)
    return CT

def KeyGen(MK,PK,Attribute:list):
    (pairing,g,h,f,root) = PK
    (beta,alpha) = MK
    beta = Element(pairing,Zr,beta)
    alpha = Element(pairing,Zr,alpha)
    randomness = Element.random(pairing,Zr)
    randomness = Element(pairing,Zr,value = 114514)
    D = g**((alpha + randomness)*(~beta))

    DList = dict()
    DList_ = dict()
    for j in Attribute:
        randomnessj = Element.random(pairing,Zr)
        randomnessj = Element(pairing,Zr,value = 123456)
        Dj = {j:(g**randomness)*(Element.from_hash(pairing,G1,j)**randomnessj)}
        Dj_ = {j:g**randomnessj}
        DList.update(Dj)
        DList_.update(Dj_)
    #print(beta*((alpha + randomness)*~beta))
    #print(alpha+randomness)
    SK = (D,DList,DList_)
    return SK,randomness

def Decrypt(CT,SK):
    (T,C_Main,C,CList,Clist_) = CT
    (D,DList,DList_) = SK
    SK_attribute = list(DList.keys())#密钥具有的属性
    path , _ =find_path(T,SK_attribute)
    result = DecryptNode(path,SK,CT)
    
    result = (C_Main)-(pairing.apply(C,D)-result)
    
    return result

def DecryptNode(node:Node,SK,CT):
    if node.leave == True:#是叶节点
        j = node.value
        (D,DList,DList_) = SK
        (T,C_Main,C,CList,Clist_) = CT
        numerator = pairing.apply(DList[j],CList[j])
        denominator = pairing.apply(DList_[j],Clist_[j])
        result = numerator - denominator

    else:#非叶节点
        Interpolation_points = []#插值点的值
        Fx = Element.one(pairing,GT)
        for i in node.children_nodes:#求子节点的值
            Interpolation_points.append(DecryptNode(i,SK,CT))
        for i in range(len(Interpolation_points)):
            Fx = Fx * (Interpolation_points[i] ** Interpolate(0,i+1,degree=len(Interpolation_points)-1))
            #print("degree:",len(Interpolation_points)-1)
        result = Fx
    return result

def Interpolate(x,j,degree):
    if type(x) == int:
        x = Element(pairing,Zr,value=x)
    point_x = [Element(pairing,Zr,value=_) for _ in range(degree + 2)]
    fenzi = Element.one(pairing,Zr)
    fenmu = Element.one(pairing,Zr)
    for i in range(1,degree + 2):
        if i == j:
            continue
        #print(i,j)
        fenzi = fenzi * (x - point_x[i])
        
        fenmu = fenmu * (point_x[j] - point_x[i])
    return fenzi*(~fenmu)



def GetGT(pairing=pairing,message = None):
    if message == None:#随机选取  
        return pairing.apply(Element.random(pairing,G1),Element.random(pairing,G1))

def Handle_Attribute(Attribute:list):
    """
    处理属性,主要是将数值型属性进行转换
    """
    bits = 3
    Attribute_Handled = []
    for i in Attribute:
        if "=" in i:
            attribute ,value = i.split("=")
            
            value = bin(int(value))[2:].zfill(bits)#bits是位数
            print(value)
            attribute_per_bit= []
            for j in range(bits):
                temp = f"{attribute}[{j}]:{value[bits-1-j]}"
                attribute_per_bit.append(temp)
            Attribute_Handled = Attribute_Handled + attribute_per_bit
        else:
            Attribute_Handled.append(i)
    return Attribute_Handled
PK,MK = Setup()#初始化，生成公钥、主密钥

#command = "D and ( A or ( B or C )  )"#命令
command = "( D and A ) or C"
AccessTree = build(command)#构建一个访问控制树
print("AccessTree:")
AccessTree.ShowNode()
Message = GetGT()#生成明文
print("Message:",Message)
CT = Encrypt(PK,M=Message,T=AccessTree)#加密
(T,C_Main,C,CList,CList_) = CT
T.ShowNode()
(pairing,g,h,f,root) = PK
#Attribute = ["A","B","C=5","D","E"]
#Attribute = Handle_Attribute(Attribute)
Attribute = ["D","A","C"]
print(Attribute)

SK,randomness = KeyGen(MK,PK,Attribute)#分发私钥

re = Decrypt(CT,SK)#解密
print("DecResult:",re)