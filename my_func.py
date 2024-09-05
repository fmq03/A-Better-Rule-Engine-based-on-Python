# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 20:53:24 2020
Edited on 2023.6.5
其他有用的函数

"""

import re

def get_op_type(condition):
    keyoperator = ["!=", ">=", "<=", "=", "<", ">"]
    for index, op in enumerate(keyoperator):
        if re.search(op, condition) is not None:
            return index
    print("条件错误，在\"",condition,"\"中无关系符号(=,>,<..)")
    return None


   
def judge(para1, para2, op_flag=3):
    try:
        if op_flag == 3:  # 做相等运算，对应“==”
            return para1 == para2
        elif op_flag == 4:  # 做大小比较，对应“<”
            return para1 < para2
        elif op_flag == 5:
            return para1 > para2
        elif op_flag == 0:
            return para1 != para2
        elif op_flag == 1:
            return para1 >= para2
        elif op_flag == 2:
            return para1 <= para2
        else:
            print(f'{op_flag} not found')
    except TypeError:
        print("judge type error, string can't be compared to int. Please check the rule.txt or input")
    
if __name__=="__main__":       
    if(judge(2,1,get_op_type("<"))):
        print("ok")
    else:
        print("no")
        
    