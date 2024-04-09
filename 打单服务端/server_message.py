import json

import constants


# new_msg_data = {
#         "order_id":"订单编号",
#         "record_id":"编号",
#         "address": 地址,
#         "content": 货物内容,
#         "cur_time": 打单时间 格式为 2024-03-04 12:00:00,
#         "cur_man":打单人,
#         "cur_progress:当前进度": constants.PRINT
#     }
# }

def message_content(data):
    content = {
        "type": "template",
        "data": {
            "template_id": "ctp_AAkMFELr1kYJ",
            "template_variable": data
        }

    }

    # 将字典转换为JSON字符串
    json_string = json.dumps(content, ensure_ascii=False)
    return json_string
