import requests
import constants
from server import app



def get_tenant_access_token(app_id, app_secret):
    url_tat = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    post_data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    r = requests.post(url_tat, data=post_data)
    return r.json()["tenant_access_token"]


def do_write_one_record(record_data):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url_write = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
                 + constants.FEISHU_TABLE_NAME_ONLINE + "/records")
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    r_write = requests.post(url_write, headers=header, json=record_data)
    return r_write.json()


def write_one_record(data):
    ok = False
    try:
        app.logger.info("call_remote_service_async request data", data)
        # 模拟异步地请求远程服务
        response = do_write_one_record(data)  # 假设这里是你的异步HTTP请求
        app.logger.info("call_remote_service_async response data", response)

        if response["code"] == 0:  # 假定当响应码为0时表示成功
            # server_db.update_order_status(constants.LOCAL_DATA_UPDATE_ING, order_id)
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



def read_records():
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + constants.FEISHU_TABLE_NAME_ONLINE + "/records/search")
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
    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + constants.FEISHU_TABLE_NAME_ONLINE + "/records/search")
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


def delete_records(record_ids):
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/"
           + constants.FEISHU_TABLE_NAME_ONLINE + "/records/batch_delete")
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

    # {
    #     "filter": {
    #         "conjunction": "and",
    #         "conditions": [
    #             {
    #                 "field_name": "手机号码",
    #                 "operator": "is",
    #                 "value": [
    #                     "15500000001"
    #                 ]
    #             },
    #             {
    #                 "field_name": "密码",
    #                 "operator": "is",
    #                 "value": [
    #                     "888"
    #                 ]
    #             }
    #         ]
    #     }
    # }
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
            code = -1
            app.logger.info("Remote service call failed with status code:", res["code"])
    except requests.HTTPError as e:
        app.logger.info(f"An HTTP error occurred: {e}")
    except Exception as e:
        app.logger.info(f"An error occurred: {e}")
    return code, name
