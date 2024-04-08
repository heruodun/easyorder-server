import json
import requests
import xlwings as xw
import time
from datetime import datetime


def new_write_one_record(new_record_data):
    url = 'http://127.0.0.1:5000/orders'
    response = requests.post(url, json=new_record_data)
    data = response.json()
    order_id,order_create_time = data["order_id"],data["create_time"]
    print(order_create_time, order_id)
    return order_id,order_create_time



# 调用入口 保存并打印
def save_print():
    new_record_data = get_excel_value()
    order_id,order_create_time = new_write_one_record(new_record_data)
    set_excel_value(order_id,order_create_time)

# 从excel读取需要保存和打印的数据
def get_excel_value():
    wb = xw.Book.caller()

    A12_E26 = wb.sheets[0].range("A12:E26").value

    # 规格数据
    guige = A12_E26[3][0]
    # 备注数据
    beizhu = A12_E26[3][4]
    # 地址数据
    dizhi = A12_E26[0][1]
    # 创单人员
    man=A12_E26[14][1]
    # 长度数据
    # 条数数据
    str_l_d = "{"
    for i in range(0,10):
        str_l_d = str_l_d + str(A12_E26[i + 3][1]) + ":" + str(A12_E26[i + 3][3]) + ","
    str_l_d = str_l_d + "}"

    new_record_data = {
        "printer": man,
        "address": dizhi,
        "content": "[规格：" + guige + "],[长度和条数：" + str_l_d + "],[备注：" + beizhu + "]",
    }
    return new_record_data





# 回写数据到excel
def set_excel_value(order_id,order_create_time):
    wb = xw.Book.caller()
    wb.sheets[0].range("E5").value = order_id + "$xiaowangniujin"
    wb.sheets[0].range("E26").value = order_id
    wb.sheets[0].range("D26").value = order_create_time



if __name__ == "__main__":

    for i in range(0,10):
        data = {
            "address": "富强100发发",
            "content": "[2,4-3,9-8]",
            "printer": "杨 Doe",
        }

        start_time = datetime.now()
        new_write_one_record(data)
        end_time = datetime.now()    # 2023年1月1日12点30分
        elapsed_time = end_time - start_time
        print(elapsed_time)  # 输出: 0:02:30

        new_record_data = {
            "fields": {
                "创单人员": "小明",
                "当前进度": "送货",
                "地址": "富强3号",
                "货物": "[usax],[68:87,99:90,1:1],[]",
                "总体进度": "[出货,2024-12-12 12:00:00,小明],[进货,2024-12-12 12:00:00,小明]"
            }
        }
        start_time = datetime.now();
        end_time = datetime.now()    # 2023年1月1日12点30分
        elapsed_time = end_time - start_time
        print(elapsed_time)  # 输出: 0:02:30
