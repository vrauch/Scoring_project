import os
os.chdir('C:/Users/kaosh/Desktop/Side-project-ML/sentence_analyze')  # 換路徑使用

import openpyxl
wb = openpyxl.load_workbook('TCB Response.xlsx')     # 開啟 Excel 檔案

names = wb.sheetnames    # 讀取 Excel 裡所有工作表名稱
s1 = wb['DevOps']        # 取得工作表名稱為「工作表1」的內容
s2 = wb['Criteria']           # 取得開啟試算表後立刻顯示的工作表 ( 範例為工作表 2 )

#print(names)
# 印出 title ( 工作表名稱 )、max_row 最大列數、max_column 最大行數
#print(s1.title, s1.max_row, s1.max_column)
#print(s2.title, s2.max_row, s2.max_column)


#print(s1.cell(1, 11).value)   # 等同取出 A1 的內容

def get_values(sheet):
    arr = []                      # 第一層串列
    for row in sheet:
        arr2 = []                 # 第二層串列
        for column in row:
            arr2.append(column.value)  # 寫入內容
        arr.append(arr2)
    return arr
#print(get_values(s1))       # 印出工作表 1 所有內容
#print(get_values(s2))       # 印出工作表 2 所有內容

v = s2.iter_rows(min_row=2, min_col=3, max_col=4)
criteria = []
for i in v:
    tmp = []
    for j in i:
        tmp.append(j.value)
    criteria.append(tmp)

print(criteria[0][1])



'''
criteria = []
for row in s2:
    tmp = []
    for column in row:
        tmp.append(column.value)
    criteria.append(tmp)

print(criteria[1][2])
print(criteria[1][3])

for i in range(10, len(s1), 2):
    for j in range()
    if s1.cell(1, i).value in criteria:

'''
