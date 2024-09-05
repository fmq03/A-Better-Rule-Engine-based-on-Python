# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 20:24:03 2020
以一定格式写下规则文件，保存为txt格式，用ruletable类来消化这种格式的规则
目前只支持每条规则最多两个条件，两个条件间的逻辑运算只支持and 和 or
条件值只接受string，bool，int,float类型，输出目前只支持等于操作符
"""

import re
import numpy as np
import pandas as pd
from my_func import get_op_type
from my_func import judge

keyoperator = ["!=", ">=", "<=", "=", "<", ">"]


class ruletable:
    rule_list = None
    rule_table = None

    def __init__(self, filename):
        with open(filename, 'r', encoding="utf-8") as f:
            self.rule_list = f.readlines()  # 将规则文件的每一行读入列表
        self.rule_table = pd.DataFrame(
            np.zeros((len(self.rule_list), 9)),
            columns=[
                "input_type1",
                "input_value1",
                "input_type2",
                "input_value2",
                "relationship1",
                "relationship2",
                "input_relationship",
                "result_type1",
                "result_value1",  # "result_type2", "result_value2",
                # "result_relationship1", "result_relationship2"
            ],
        )
        self.fill_table()  # 填充规则表
        self.result = {}

    def conv_type(self, typeflag, val):
        if typeflag == 'int':  # 类型为int
            return int(val)
        elif typeflag == 'bool':  # 类型为bool
            return bool(int(val))
        elif typeflag == 'float':  # 类型为float
            return float(val)
        else:
            return val

    def analyse_expression(self, expression):
        typeflag = 'string'
        if re.search('\(', expression) != None:  # 包含括号则说明有指定类型，不包含则默认为string类型
            typeflag = expression[(expression.index('(')) +1: (expression.index(')'))]  # 通过括号内字符的内容来确定类型
        expression = re.sub(r'\([a-zA-Z]+\)', '', expression)  # 删除括号和括号内的内容
        relationship = get_op_type(expression)
        content = re.split(keyoperator[relationship], expression)
        content[0] = content[0].strip()
        content[1] = content[1].strip()  # str.strip()去除首尾空格
        # print(f'{typeflag} of {content[1]}')
        return (
            relationship,
            content[0],
            self.conv_type(typeflag, content[1])
        )  # 分别返回关系符、左值、右值

    def write_condition(self, index, expression, condition_num):
        relationship, left, right = self.analyse_expression(expression)
        self.rule_table.loc[index, 'relationship' + str(condition_num)] = relationship
        self.rule_table.loc[index, 'input_type' + str(condition_num)] = left
        self.rule_table.loc[index, 'input_value' + str(condition_num)] = right
        # print(f'value:{right}\'s type: {type(right)}' )

    def write_result(self, index, expression):
        relationship, left, right = self.analyse_expression(expression)
        self.rule_table.loc[index, 'result_type1'] = left
        self.rule_table.loc[index, 'result_value1'] = right

    def fill_table(self):
        '''
        根据txt文件生成规则表，以供查询
        '''
        index = 0  # 从索引号开始填表
        tmpvar_index = 0
        for con_res in self.rule_list:
            cr = con_res.split(" then ")  # 将条件和结果部分分开
            conditions = cr[0]
            conditions = conditions[3:]

            stack = []  #通过中缀表达式转后缀表达式的方式，重新解析条件部分，并存储到postfix数组中
            postfix = []
            cur = 0
            for i in range(len(conditions)):
                if conditions[i] == "[": #左括号直接进栈
                    stack.append('[')
                    cur = i + 1
                elif conditions[i] == "]":  #右括号先处理括号前面的一个表达式
                    if cur != i:
                        tmp = conditions[cur:i]
                        postfix.append(tmp)
                    cur = i + 1
                    while stack and stack[-1] != '[': #然后将所有内容出栈，直到遇到左括号
                        postfix.append(stack.pop())
                    stack.pop()  # 弹出左括号 
                elif conditions[i : i + 5] == ' and ': #and先处理and之前的一个表达式 
                    if cur != i:
                        tmp = conditions[cur:i]
                        postfix.append(tmp)
                    cur = i + 5
                    while stack and stack[-1] != '[' and stack[-1] != 'or': #将所有优先级等于或高于and的内容出栈（括号除外）（这个里面只有and）
                        postfix.append(stack.pop())
                    stack.append('and') 
                elif conditions[i : i + 4] == ' or ': #先处理or之前的一个表达式
                    if cur != i:
                        tmp = conditions[cur:i]
                        postfix.append(tmp)
                    cur = i + 4
                    while stack and stack[-1] != '[': #将所有优先级等于或高于or的内容出栈（括号除外）（这个程序中and or都算，只有括号不是）
                        postfix.append(stack.pop())
                    stack.append('or')
            if cur != len(conditions): #处理末尾的一个表达式
                tmp = conditions[cur::]
                tmp = tmp.rstrip()
                postfix.append(tmp)
            while stack:  #如果栈不空，出栈所有元素
                postfix.append(stack.pop())
            print(postfix)

            stack = []     #解析后缀表达式，将多个条件拆成两个两个的条件，并添加中间变量TMPVARxx 最后finalcondition留下唯一的条件给真正的结果
            finalcondition = ''
            for elem in postfix:
                if elem == 'and' or elem == 'or': #如果是and 或者or，就弹出两个条件，并让结果为一个中间变量TMPVARxx
                    a = stack.pop()
                    b = stack.pop()
                    self.write_condition(index, a, 1)
                    self.write_condition(index, b, 2)
                    self.rule_table.loc[index, 'input_relationship'] = 1 if elem=='and' else 2
                    result_tmp = 'TMPVAR' + str(tmpvar_index) + ' = ' + 'True'
                    tmpvar_index += 1
                    self.write_result(index, result_tmp)
                    finalcondition = result_tmp
                    stack.append(result_tmp)
                    print("RULE NO.", index, "has been built")
                    index += 1
                else:
                    stack.append(elem)
                    finalcondition=elem

            res = re.split("and", cr[1])   #解析任意多个结果并写入
            # self.fill_conditions_or_results(2, index, res)
            result_num = 0
            for result in res:  #条件是finalcondition，结果逐个写入一条规则
                self.write_condition(index,finalcondition,1)
                self.write_result(index,result.strip())
                print("RULE NO.", index, "has been built")
                index += 1
        print(self.rule_table)

    def find_tag(self, tag):
        '''
        根据tag来找到对应的规则在table表中的行索引号，返回一个int列表，如果没有匹配项则返回None
        '''
        rule = self.rule_table.copy()
        indexlist = rule[(rule["input_type1"] == tag) | (rule["input_type2"] == tag)].index
        return indexlist

    def condition_judge(self, index, case):
        '''
        对于一个case，判断在rule_table中第index行的条件是否满足，返回bool值
        '''
        rule = self.rule_table.copy()
        condition_type1 = rule.loc[index, "input_type1"]
        condition_value1 = rule.loc[index, "input_value1"]
        condition_value2 = rule.loc[index, "input_value2"]
        condition_type2 = rule.loc[index, "input_type2"]
        op_flag1 = rule.loc[index, 'relationship1']
        op_flag2 = rule.loc[index, 'relationship2']
        if rule.loc[index, "input_relationship"] == 1:  # 对两个条件做与运算
            if case.get(condition_type2) and case.get(condition_type1):  # 两个标签在case中都存在
                bool1 = judge(case[condition_type1], condition_value1, op_flag1)
                bool2 = judge(case[condition_type2], condition_value2, op_flag2)
                if bool1 and bool2:
                    return True
        elif rule.loc[index, "input_relationship"] == 2:
            if case.get(condition_type2) and case.get(condition_type1):  # 两个标签在case中都存在
                bool1 = judge(case[condition_type1], condition_value1, op_flag1)
                bool2 = judge(case[condition_type2], condition_value2, op_flag2)
                if bool1 or bool2:
                    return True
        else:  # 剩下的情况逐个判断即可
            if case.get(condition_type2):
                bool2 = judge(case[condition_type2], condition_value2, op_flag2)
                return bool2
            if case.get(condition_type1):
                bool1 = judge(case[condition_type1], condition_value1, op_flag1)
                return bool1
        return False

    def reason_one_time(self, case):
        '''
        输入case为一个字典类型，输出经过规则表之后得到的结果（字典格式）
        '''
        keys = case.keys()  # 保存所有要匹配的标签到keys，用于后续查找
        for k in keys:
            indexlist = self.find_tag(k)
            if indexlist.size < 1:
                continue  # 如果没有找到此标签的规则，那么进行下一标签的查找
            for i in indexlist:
                if self.condition_judge(i, case):  # if the condition is satisfied, then add the result info according to the rule table
                    result_type1 = self.rule_table.loc[i, 'result_type1']
                    result_value1 = self.rule_table.loc[i, 'result_value1']
                    self.result[result_type1] = result_value1
        return self.result

    def reason(self, case):
        temp_case = case.copy()
        while True:
            length1 = len(temp_case)
            result = self.reason_one_time(temp_case)  # 进行一次规则匹配
            self.result.update(result)  # 更新当前result列表
            temp_case.update(result)
            length2 = len(temp_case)
            if length2 == length1:  # 结果列表中无新成员
                break
        ans={}
        print(self.result)
        for result_type in self.result:
            if(result_type.find('TMPVAR')==-1):
                ans[result_type]=self.result[result_type]
        return ans


if __name__ == '__main__':
    rt = ruletable("RULE1.txt")
    rule_table = rt.rule_table
    case = {'personality': 'kind', 'sex': 'male' ,'age':19}
    result = rt.reason(case)  # 进行遍历
    print(result)
