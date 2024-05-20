import warnings
# 忽略 DeprecationWarning 警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pickle
from pypbc import Element,Parameters,Pairing,G1,Zr,GT
from tree import Node,build,get_leaves,find_path
from typing import Union,Tuple

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
#params = Parameters(qbits=10, rbits=10)
pairing = Pairing(params)

class Node:
    def __init__(self,value=None):
        self.value = value
        self.children_nodes=[]  #子节点
        self.parent = None      #父节点
        self.gate = None        #逻辑门(and,or)
        self.depth = 0          #节点的深度
        self.leave = True       #是否为叶节点
        self.qx = 0             #qx(0)
        self.kx = 0             #threshold
        self.dx = 0
        self.Cy = 0
        self.Cy_ = 0
        if value == "and":
            self.gate = "and"
        elif value == "or":
            self.gate = "or"
    def AddChild(self,child_node:'Node',change_depth=False):
        self.children_nodes.append(child_node)
        self.leave = False
        child_node.parent = self#为该子节点设置父节点
        if change_depth == True:#需要修改节点深度数据
            self.ChangeDepth(self)
    def ChangeDepth(self):
        if self.leave == True:#是叶节点
            return
        for i in self.children_nodes:
            i.depth = self.depth + 1 
            if i.leave == False:#子节点不是叶节点
                i.ChangeDepth()
    def ShowNode(self):
        print("value:",self.value,"depth:",self.depth,"cipher:",self.Cy)
        for i in range(len(self.children_nodes)):
            print(f"{self.value}'s children{i}:")
            self.children_nodes[i].ShowNode()
def combine(node1,gate,node2,value):
    this_node = Node(value)
    this_node.gate=gate
    this_node.AddChild(node1)
    this_node.AddChild(node2)
    return this_node

def show_cmd_list(cmdlist):
    for i in cmdlist:
        if type(i) == Node:
            print(i.value,end=" ")
        else:
            print(i,end=" ")
    print()

def build(command,notleaveidx=0,newnode=True):
    stack = []
    cmdlist = command.split()
    notleaveidx = 0
    for i in range(len(cmdlist)):
        if cmdlist[i] not in ["and","or","(",")"]:#i是属性节点
            if "<=" in cmdlist[i]:
                cmdlist[i] = handle_int(cmdlist[i].split("<=")[0],"<=",cmdlist[i].split("<=")[1])
            elif ">=" in cmdlist[i]:
                cmdlist[i] = handle_int(cmdlist[i].split(">=")[0],">=",cmdlist[i].split(">=")[1])
            elif "=" in cmdlist[i]:
                cmdlist[i] = handle_int(cmdlist[i].split("=")[0],"=",cmdlist[i].split("=")[1])
            elif "<" in cmdlist[i]:
                cmdlist[i] = handle_int(cmdlist[i].split("<")[0],"<",cmdlist[i].split("<")[1])
            elif ">" in cmdlist[i]:
                cmdlist[i] = handle_int(cmdlist[i].split(">")[0],">",cmdlist[i].split(">")[1])
            else:#非数值型节点
                cmdlist[i] = Node(cmdlist[i])
    
    #stack = command.split()#把指令存入栈
    while len(cmdlist):#列表非空
        cmd = cmdlist.pop(0)

        if cmd == ")":#右括号，开始出栈
            if stack[-2] == "(":#节点的左边就是括号，例如 (A) 这种形式，直接返回
                this_node = stack.pop()
                
            else:
                while stack[-2] != "(":
                    node2 = stack.pop()#取出节点2
                    gate = stack.pop() #取出逻辑门
                    node1 = stack.pop()#取出节点1
                    this_node = combine(node1,gate,node2,value=gate)
                    notleaveidx += 1 
                    stack.append(this_node)
                this_node = stack.pop()
            stack.pop()#把左括号取出来
            stack.append(this_node)
        else:          #入栈
            stack.append(cmd)
    
    while len(stack)>1:#栈中元素数量多于1
        node2 = stack.pop()#取出节点2
        gate = stack.pop() #取出逻辑门
        node1 = stack.pop()#取出节点1
        this_node = combine(node1,gate,node2,value=gate)
        stack.append(this_node)
    return stack[0]

def handle_int(sample,operator,value):
    value = int(value)
    bits = 16
    if operator == ">":#转换成 >= 运算
        value = value + 1
        operator = ">="
        return int2logic(sample,operator,bin(value)[2:].zfill(bits))
    elif operator == "<":#转换成 <= 运算
        value = value - 1
        operator = "<="
        return int2logic(sample,operator,bin(value)[2:].zfill(bits))
    elif operator == ">=":
        return int2logic(sample,operator,bin(value)[2:].zfill(bits))
    elif operator == "<=":
        return int2logic(sample,operator,bin(value)[2:].zfill(bits))
    elif operator == "=":
        this_node = Node("and")
        childnode1 = int2logic(sample,"<=",bin(value)[2:].zfill(bits))
        childnode2 = int2logic(sample,">=",bin(value)[2:].zfill(bits))
        this_node.AddChild(childnode1)
        this_node.AddChild(childnode2)
        return this_node
    
def int2logic(sample,operator,value):
    if operator == "<=":
        bin_upper_bound = value

        for i in range(len(bin_upper_bound)):
            if bin_upper_bound[0] == "1":#用或门
                this_node = Node("or")

            elif bin_upper_bound[0] == "0":
                this_node = Node("and")

            if "0" not in bin_upper_bound[1:]:#低位全是1，只需要当前位是0即可满足所有条件
                this_node = Node(sample + f"[{len(bin_upper_bound)-1-i}]:0")
                return this_node
            else:
                childnode1 = Node(sample + f"[{len(bin_upper_bound)-1-i}]:0")
                childnode2 = int2logic(sample,operator,bin_upper_bound[i+1:])
                this_node.AddChild(childnode1)
                this_node.AddChild(childnode2)
                return this_node
    elif operator == ">=":
        bin_lower_bound = value

        for i in range(len(bin_lower_bound)):
            if bin_lower_bound[0] == "0":#用或门
                this_node = Node("or")

            elif bin_lower_bound[0] == "1":
                this_node = Node("and")

            if "1" not in bin_lower_bound[1:]:#低位全是0，只需要当前位是1即可满足条件
                this_node = Node(sample + f"[{len(bin_lower_bound)-1-i}]:1")
                return this_node
            else:
                childnode1 = Node(sample + f"[{len(bin_lower_bound)-1-i}]:1")
                childnode2 = int2logic(sample,operator,bin_lower_bound[i+1:])
                this_node.AddChild(childnode1)
                this_node.AddChild(childnode2)
                return this_node

def get_leaves(node:Node):
    if node.leave == True:
        return [node.value]
    else:
        leaves = []
        for i in node.children_nodes:
            leaves = leaves + get_leaves(i)
        return leaves
def get_weight(node:Node)->int:
    return len(get_leaves(node))

def find_path(node:Node,attribute:list=[],depth = 0) -> Tuple[Union[Node,None],int]:
    """
    根据属性寻找是否有符合的路径
    返回(最佳路径节点,所需属性数量)
    """
    if node.leave == True:  #是叶节点
        if node.value in attribute:#具有该属性
            node.depth = depth
            return node,1
        else:#不具有该属性，此路径不合法
            return None,0
    else:                   #非叶节点
        if node.gate == "or": #或门
            #TODO:当两条路径的weight一样时，应当选择depth较浅的那条路，但是现在这样也可以用
            path = Node("or")
            result_node = None

            for i in node.children_nodes:
                i_node,i_weight = find_path(i,attribute=attribute,depth=depth+1)
                if None == i_node:#此路径非法
                    continue
                if result_node == None:
                    result_node = i_node
                    result_weight = i_weight
                elif result_weight >= i_weight:#有更好的路径
                    result_node = i_node
                    result_weight = i_weight
            if result_node == None:#没找到任何一条合法路径
                return None,0
            path.AddChild(result_node)
            return path,result_weight
        
        if node.gate == "and": #与门
            path = Node("and")
            result_weight = 0
            for i in node.children_nodes:

                i_node,i_weight = find_path(i,attribute=attribute,depth=depth+1)
                if None == i_node:#此路径非法
                    return None,0
                i_node,i_weight = find_path(i,attribute=attribute,depth=depth+1)
                result_weight += i_weight
                path.AddChild(i_node)
            return path,result_weight
        


def Setup(qbits=512,rbits=160):
    """
    初始化,返回(PK,MK)
    """
    params = Parameters(param_string = params_A)
    pairing = Pairing(params)
    g = Element.random(pairing,G1)
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
        #coe = [qr0,Element(pairing,Zr,value = 3)]
        #coe = [qr0,Element.random(pairing,Zr)]
        coe = [qr0]
        for i in range(T.kx-1):
            coe.append(Element.random(pairing,Zr))
        def f(x,coe=coe):
            result = Element.zero(pairing,Zr)
            for i in range(len(coe)):
                result += coe[i] * pow(x,i)
            return result

        for i in range(0,len(T.children_nodes)):
            Cy,Cy_ = choose_poly(PK,T.children_nodes[i],qr0=f(i+1))
            CList.update(Cy)
            CList_.update(Cy_)
    return CList,CList_

def Encrypt(PK,M,T:Node):
    (pairing,g,h,f,root) = PK
    s = Element.random(pairing,Zr)
    C_Main = M+(root**s)#*M #pow(root,s) * M#主密文
    C = h ** s
    CList,CList_=choose_poly(PK,T,s)

    CT = (T,C_Main,C,CList,CList_)
    return CT

def KeyGen(MK,PK,Attribute:list):
    Attribute = Handle_Attribute(Attribute)
    (pairing,g,h,f,root) = PK
    (beta,alpha) = MK
    beta = Element(pairing,Zr,beta)
    alpha = Element(pairing,Zr,alpha)
    randomness = Element.random(pairing,Zr)
    D = g**((alpha + randomness)*(~beta))

    DList = dict()
    DList_ = dict()
    for j in Attribute:
        randomnessj = Element.random(pairing,Zr)
        Dj = {j:(g**randomness)*(Element.from_hash(pairing,G1,j)**randomnessj)}
        Dj_ = {j:g**randomnessj}
        DList.update(Dj)
        DList_.update(Dj_)
    SK = (D,DList,DList_)
    return SK,randomness

def Decrypt(CT,SK):
    (T,C_Main,C,CList,Clist_) = CT
    (D,DList,DList_) = SK
    SK_attribute = list(DList.keys())#密钥具有的属性
    path , _ = find_path(T,SK_attribute)
    #path.ShowNode()
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
    bits = 16
    Attribute_Handled = []
    for i in Attribute:
        if "=" in i:
            attribute ,value = i.split("=")
            value = bin(int(value))[2:].zfill(bits)#bits是位数
            attribute_per_bit= []
            for j in range(bits):
                temp = f"{attribute}[{j}]:{value[bits-1-j]}"
                attribute_per_bit.append(temp)
            Attribute_Handled = Attribute_Handled + attribute_per_bit
        else:
            Attribute_Handled.append(i)
    return Attribute_Handled
if __name__ == "__main__":
    PK,MK = Setup()
    command = "( ( A and C ) or ( B and D ) ) and E<5"
    AccessTree = build(command)
    Message = GetGT()
    print("Message:",Message)
    CT = Encrypt(PK,M=Message,T=AccessTree)
    (T,C_Main,C,CList,CList_) = CT
    (pairing,g,h,f,root) = PK
    Attribute = ["B","A","D","E=1"]
    SK,randomness = KeyGen(MK,PK,Attribute)
    (D,DList,DList_) = SK
    re = Decrypt(CT,SK)
    print(re)
    print(re == Message)
