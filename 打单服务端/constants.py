import os
import re
from pypinyin import lazy_pinyin

# 对接收货或者送货状态删除的天数
DONE_DELETE_DATA_DAY = 14
# 全部单子的删除天数
ALL_DELETE_DATA_DAY = 30
# 角色常量，英文变量名对应中文值
PRINT = "打单"
PICK = "配货"
DELIVERY = "送货"
COORDINAT = "对接"
RECEIVE = "对接收货"

# 远程数据已被删除
REMOTE_DATA_HAS_DELETED = 100
# 预备删除态，下一步就是删除远程数据
REMOTE_DATA_TO_BE_DELETE = 99
# 已经到发货状态，可以删除远程数据
REMOTE_DATA_CAN_BE_DELETE = 98
# 远端数据更新到本地
REMOTE_DATA_UPDATE_LOCAL = 2
# 本地数据第一次插入到远端
LOCAL_DATA_FIRST_INSERT = 1
# 初始化
LOCAL_DATA_INIT = 0

COMPANY_NAME = "小王牛筋"

QR_CODE_SUFFIXES = "$xiaowangniujin"

JOB_ONE = "job1_delete_feishu"
JOB_TWO = "job2_insert_feishu"

FEISHU_TABLE_NAME_ONLINE = "tblBmGg1sYkSV9GC"

FEISHU_TABLE_NAME_TEST = "tbldwOe9EHil0YtN"

FEISHU_TABLE_CHAT_ONLINE = "oc_8bfc53fcc82aa85ee5c23ae64ce4ae8b"

FEISHU_TABLE_CHAT_TEST = "oc_408054f11251acb94985eacc794bcaf0"

SERVER_ENV_KEY = "ORDER_EASY_SERVER_ENV"

# 条数与总条数不一致
INSERT_ERROR_CODE_1 = 10001
# 条数不是整数
INSERT_ERROR_CODE_2 = 10002
# 总长度不是整数
INSERT_ERROR_CODE_3 = 10003
# 地址不在地址库
INSERT_ERROR_CODE_4 = 10004
# 长度为空
INSERT_ERROR_CODE_5 = 10005


def get_inset_err_msg(code):
    if code == INSERT_ERROR_CODE_1:
        return "总条数不正确"
    if code == INSERT_ERROR_CODE_2:
        return "条数不是整数"
    if code == INSERT_ERROR_CODE_3:
        return "总长度不是整数"
    if code == INSERT_ERROR_CODE_4:
        return "地址不在地址库"
    if code == INSERT_ERROR_CODE_5:
        return "长度为空"


def get_feishu_table():
    if os.getenv('ORDER_EASY_SERVER_ENV') == 'online':
        return FEISHU_TABLE_NAME_ONLINE
    elif os.getenv('ORDER_EASY_SERVER_ENV') == 'test':
        return FEISHU_TABLE_NAME_TEST
    else:
        return ""


def get_feishu_chat():
    if os.getenv('ORDER_EASY_SERVER_ENV') == 'online':
        return FEISHU_TABLE_CHAT_ONLINE
    elif os.getenv('ORDER_EASY_SERVER_ENV') == 'test':
        return FEISHU_TABLE_CHAT_TEST
    else:
        return ""


def sort_key(s):
    # 将字符串中的数字增加前导零填充，以确保数字按数值排序而不是按字符串
    s = re.sub('\d+', lambda x: x.group().zfill(10), s)
    # 使用 pypinyin 库将字符串转换为拼音，未能识别的部分（如数字）将保持原样
    return lazy_pinyin(s)


# 对列表进行排序

