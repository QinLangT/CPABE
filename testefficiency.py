from pypbc import *
import random
import tree
import time
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

def LagCoe(i,S,x):
    result = 1
    for j in S:
        if j != i:
            result = result*(x-j)/(i-j)
    return result

#def L(x,y)

def Setup(qbits=512,rbits=160):
    """
    初始化,返回(PK,MK)
    """
#    params = Parameters(qbits=qbits,rbits=rbits)#参数初始化
    params = Parameters(param_string = params_A)
    pairing = Pairing(params)
    g = Element.random(pairing,G1)
    alpha = Element.random(pairing,Zr)
    beta = Element.random(pairing,Zr)
    h = g*beta  
    f = g*beta.__invert__()#f=g/beta
    root = pairing.apply(g,g)*alpha#e(g,g)^alpha
    ga = g*alpha
    PK=(pairing,g,h,f,root)
    MK=(beta,ga)
    return PK,MK

def H(s,pairing):
    """
    {0,1}*->G1
    """
    return Element.from_hash(pairing,G1,s)
PK,MK = Setup()
pairing,g,h,f,root = PK
beta,ga = MK

#KeyGen
Hj=H("test",pairing)
Rand = random.randint(0,r)
Randj = random.randint(0,r)
Dj = (g**Rand)*(Hj**Randj)
Dj_ = g**Randj

#Enc
qy0 = 114514
Cy = g**qy0
Cy_ = H("test",pairing)**qy0

#DecNode
begin = time.time()
for i in range(1000):
    fenzi = pairing.apply(Dj,Cy)
    fenmu = pairing.apply(Dj_,Cy_)
    re = fenzi - fenmu
end  = time.time()
#print(fenzi+fenmu)
print(begin,end)
t1 = end-begin
print(end-begin)

begin = time.time()
for i in range(1000):
    re = LagCoe(i=0,S=[0,1,2],x=3)*1+LagCoe(i=1,S=[0,1,2],x=3)*6+LagCoe(i=2,S=[0,1,2],x=3)*17
end  = time.time()
#print(fenzi+fenmu)
print(begin,end)
t2 = end-begin
print(end-begin)

print(t2/t1*100,"%")