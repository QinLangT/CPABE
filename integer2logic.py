from tree import *

def handle_int(sample,operator,value):
    if type(value) == int:
        value = bin(value)[2:]
    if operator == ">":#转换成 >= 运算
        value = value + 1
        operator = ">="
        return int2logic(sample,operator,value)
    elif operator == "<":#转换成 <= 运算
        value = value - 1
        operator = "<="
        return int2logic(sample,operator,value)
    elif operator == ">=":
        return int2logic(sample,operator,value)
    elif operator == "<=":
        return int2logic(sample,operator,value)
    elif operator == "=":
        this_node = Node("and")
        childnode1 = int2logic(sample,"<=",value)
        childnode2 = int2logic(sample,">=",value)
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
if __name__ == "__main__":
    a=int2logic("A",">=","1101")
    b=int2logic("A","<=","1101")    
    a.ShowNode()            
    print()
    b.ShowNode()