#
# import requests
# from datetime import datetime, timedelta
#
# # url = 'http://127.0.0.1:5000/orders'
# # data = {
# #     "address": "富强100发发",
# #     "content": "[2,4-3,9-8]",
# #     "printer": "杨 Doe",
# # }
# #
# # response = requests.post(url, json=data)
# # print(response.text)
#
# now = datetime.now()
# time_stamp_30_seconds_ago_in_millis = int((now.timestamp() - 30) * 1000)
# print(time_stamp_30_seconds_ago_in_millis)
#
#
#
import requests
import json

url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
payload = json.dumps({
    "content": "{\"zh_cn\": {\"title\": \"我是一个标题\", \"content\": [[{\"tag\": \"text\", \"text\": \"第一行:\", \"style\": [\"bold\", \"underline\"]}]]}}",
    "msg_type": "post",
    "receive_id": "oc_408054f11251acb94985eacc794bcaf0"
})


headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer t-g10449fJORUMNIBH53OMT4CND3MVX7PZTCID2XH6'
}

response = requests.request("POST", url, headers=headers, data=payload)
print(response.text)