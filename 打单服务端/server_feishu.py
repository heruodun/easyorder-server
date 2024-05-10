import json
import requests
import constants
from server import app
import server_message


def get_tenant_access_token(app_id, app_secret):
    url_tat = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    post_data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    r = requests.post(url_tat, data=post_data)
    return r.json()["tenant_access_token"]


def update_feishu_async(wave_id, cur_status, cur_time, cur_man, order_trace, wave_alias, order_id):
    ids_batch = []
    ids_batch.append(order_id)
    response_data = read_records_by_order_ids(ids_batch)
    if response_data['code'] == 0:
        # 若成功获取响应，遍历 response_data 获取每个订单ID的存在性
        for item in response_data['data']['items']:
            record_id = item['']
            record_data = {

            }

            do_update_wave(record_data)


#
# # 需要获取当前时间的格式化字符串
# current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
# # 随机数据作为范例用于测试使用
# update_order(
#     wave_id=123,
#     cur_status='拣货',
#     cur_time=current_time,
#     cur_man='操作员A',
#     order_trace='这里是变更后的订单追踪记录',
#     wave_alias='波次别名',
#     order_data={'order_id': 456}


def do_update_wave(record_data):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)

    feishu_table = constants.get_feishu_table()

    url_write = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
                 + feishu_table + "/records")
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    r_write = requests.post(url_write, headers=header, json=record_data)
    return r_write.json()


def do_write_one_record(record_data):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)

    feishu_table = constants.get_feishu_table()

    url_write = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
                 + feishu_table + "/records")
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    r_write = requests.post(url_write, headers=header, json=record_data)
    return r_write.json()


def write_one_record(data):
    ok = False
    try:
        app.logger.info("call_remote_service_async request data %s", data)
        # 模拟异步地请求远程服务
        response = do_write_one_record(data)  # 假设这里是你的异步HTTP请求
        app.logger.info("call_remote_service_async response data %s", response)

        if response["code"] == 0:  # 假定当响应码为0时表示成功

            app.logger.info("call_remote_service_async success")
            ok = True  # 请求成功，退出循环
        else:
            # 报警逻辑
            app.logger.info("call_remote_service_async failed with status code:", response["code"])
    except Exception as e:
        # 异常处理逻辑
        app.logger.info("call_remote_service_async failed", str(e))
        # 在这里可以加入报警/日志记录代码
    finally:
        return ok


def read_records(page_token, page_size):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    feishu_table = constants.get_feishu_table()

    # 将 page_size 参数转换为字符串
    page_size_str = str(page_size)

    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + feishu_table + "/records/search?page_size=" + page_size_str)
    if page_token:
        url += "&page_token=" + page_token
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    json = {
    }
    response = requests.post(url, headers=header, json=json)
    return response.json()


def read_records_by_order_ids(order_ids):
    if not order_ids:
        return "{}"
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)

    feishu_table = constants.get_feishu_table()

    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + feishu_table + "/records/search")
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    # 构建筛选条件
    conditions = [{"field_name": "订单编号", "operator": "is", "value": [id_]} for id_ in order_ids]
    json = {
        "filter": {
            "conjunction": "or",
            "conditions": conditions
        }
    }

    response = requests.post(url, headers=header, json=json)
    return response.json()


def delete_records_in_batches(record_ids, batch_size=100):
    """
    分页删除Feishu中的记录。

    :param record_ids: 要删除的记录ID列表。
    :param batch_size: 单页删除的记录数量。
    """
    # 计算分页数量
    total_records = len(record_ids)
    num_pages = total_records // batch_size + (1 if total_records % batch_size > 0 else 0)

    # 逐页删除记录
    for page in range(num_pages):
        # 计算当前页的起始索引和结束索引
        start_index = page * batch_size
        end_index = start_index + batch_size
        # 获取当前页的记录ID
        batch_to_delete = record_ids[start_index:end_index]

        # 删除当前页面的记录ID
        delete_records(batch_to_delete)
        app.logger.info(f"Deleted batch {page + 1} of {num_pages} (IDs: {batch_to_delete})")


def delete_records(record_ids):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    feishu_table = constants.get_feishu_table()
    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + feishu_table + "/records/batch_delete")
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    json = {
        "records": record_ids
    }
    response = requests.post(url, headers=header, json=json)
    return response.json()


# code -1表示失败 0表示成功
def read_users(phone, password):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps/IqF6bLQtla2KrKsDj1JcrN0cn7b/tables/tbl54NTtk5BEnycH/records/search?page_size=20"
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }

    json = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "手机号码",
                    "operator": "is",
                    "value": [
                        phone
                    ]
                },
                {
                    "field_name": "密码",
                    "operator": "is",
                    "value": [
                        password
                    ]
                }
            ]
        }
    }

    code = 0
    name = None
    try:
        response = requests.post(url, headers=header, json=json)
        res = response.json()
        app.logger.info("get user ", res)
        if res["code"] == 0:
            name = res["data"]["items"][0]["fields"]["姓名"][0]["text"]
        else:
            app.logger.error("Remote service call failed with status code:", res["code"])
    except requests.HTTPError as e:
        app.logger.error(f"An HTTP error occurred: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
    return code, name


# 分页获取地址 code -1表示失败 0表示成功
def read_addresses(page_token, page_size):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    # 将 page_size 参数转换为字符串
    page_size_str = str(page_size)

    url = (
            "https://open.feishu.cn/open-apis/bitable/v1/apps/YfZ0bTG5pahNddsk3VLcTXVwn3o/tables/tblGkLjcHmOfHG1Y/records/search?page_size=" + page_size_str)
    if page_token:
        url += "&page_token=" + page_token
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    json = {
    }
    response = requests.post(url, headers=header, json=json)
    return response.json()


# 假设items已经从响应中提取出来，像这样：
# items = response["data"]["items"]

def extract_addresses(items):
    addresses = []  # 初始化地址列表

    for item in items:
        try:
            # 从每个item中提取编号作为id
            id = item['fields']['编号']

            # 提取并拼接地址名称中的所有text，并去除前后以及中间的所有空格
            place_parts = [name['text'] for name in item['fields']['地址名称']]
            place = ''.join(place_parts).replace(' ', '')

            # 提取地址详细信息中的location作为coordinate
            coordinate = ""
            if '地址详细信息' in item['fields']:
                coordinate = item['fields']['地址详细信息']['location']

            # 将提取出的信息构建成一个元组，并添加到addresses列表中
            address = (id, place, coordinate)
            addresses.append(address)
        except Exception as e:
            app.logger.error(f"An error occurred: {e}")

    return addresses


# 调用extract_addresses函数处理items并获取结果
# addresses_list = extract_addresses(items)

# 输出结果（如果需要的话）
# for addr in addresses_list:
#     print(addr)


def read_all_addresses():
    all_addresses = []  # 初始化空列表以收集所有地址
    has_more = True
    page_token = None
    page_size = 400
    try:
        # 读取远程web服务获取数据
        while has_more:
            response = read_addresses(page_token, page_size)
            if response["code"] == 0:
                items = response["data"]["items"]
                addresses = extract_addresses(items)
                all_addresses.extend(addresses)  # 将地址添加到列表中
                has_more = response["data"]["has_more"]
                app.logger.info("Addresses are " + str(addresses))
                if has_more:
                    page_token = response["data"]["page_token"]
                else:
                    page_token = None
            else:
                has_more = False
            app.logger.info("Remote service call success with status code: %s", response["code"])
    except requests.HTTPError as e:
        app.logger.error(f"An HTTP error occurred: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
    return all_addresses


# new_msg_data = {
#         "order_id":"订单编号",
#         "record_id":"编号",
#         "address": 地址,
#         "content": 货物内容,
#         "cur_time": 打单时间 格式为 2024-03-04 12:00:00,
#         "cur_man":打单人,
#         "cur_pro:当前进度": constants.PRINT
#     }
# }
def send_one_message(data):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        "content": server_message.message_content(data),
        "msg_type": "interactive",
        "receive_id": str(constants.get_feishu_chat())
    })

    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        res = response.json()
        if res["code"] == 0:
            app.logger.info("send msg success %s", data)
        else:
            app.logger.error("send msg failed with status code: %s", res["code"])
    except requests.HTTPError as e:
        app.logger.error(f"An HTTP error occurred: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")


def send_one_alert_message(data):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        "content": json.dumps(data),
        "msg_type": "text",
        "receive_id": str(constants.get_feishu_chat())
    })

    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        res = response.json()
        if res["code"] == 0:
            app.logger.info("send msg success %s", data)
        else:
            app.logger.error("send msg failed with status code: %s", res["code"])
    except requests.HTTPError as e:
        app.logger.error(f"An HTTP error occurred: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
