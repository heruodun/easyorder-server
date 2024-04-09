# 超过14天数据需要清理
import os

OLD_DATA_DAY = 14
# 角色常量，英文变量名对应中文值
PRINT = "打单"
PICK = "配货"
DELIVERY = "送货"
COORDINAT = "对接"
RECEIVE = "对接送货"

# 远程数据已被删除
REMOTE_DATA_HAS_DELETED = 100
# 预备删除态，下一步就是删除远程数据
REMOTE_DATA_TO_BE_DELETE = 99
# 已经到发货状态，可以删除远程数据
REMOTE_DATA_CAN_BE_DELETE = 98
# 本地数据第一次插入到远端
LOCAL_DATA_FIRST_INSERT = 1
# 初始化
LOCAL_DATA_INIT = 0

COMPANY_NAME = "小王牛筋"

JOB_ONE = "job1_delete_feishu"
JOB_TWO = "job2_insert_feishu"

FEISHU_TABLE_NAME_ONLINE = "tblBmGg1sYkSV9GC"

FEISHU_TABLE_NAME_TEST = "tbldwOe9EHil0YtN"

FEISHU_TABLE_CHAT_ONLINE = "oc_8bfc53fcc82aa85ee5c23ae64ce4ae8b"

FEISHU_TABLE_CHAT_TEST = "oc_408054f11251acb94985eacc794bcaf0"

SERVER_ENV_KEY = "ORDER_EASY_SERVER_ENV"


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
