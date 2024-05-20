import pickle
from typing import Union,Tuple
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
        

if __name__ == "__main__":
    command = " ( ( ( A and B ) or C ) and D ) and E"
    #command2 = "( ( ( ( A and B ) or C ) or D ) or E ) and F"
    command2 = "( ( ( ( A and B ) or C ) or D ) or E ) or ( ( F and G>5 ) and H )"
    #command = "( B or C )"
    n=build(command2)
    print(get_leaves(n))
    n.ChangeDepth()
    n.ShowNode()
    attribute = ["A","B","C","D","E","F"]
    path,_ = find_path(n,attribute=attribute)
    print()
    path.ShowNode()
    print(path)
    print(pickle.dumps(path))
    path = pickle.loads(pickle.dumps(path))
    path.ShowNode()