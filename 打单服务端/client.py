
import requests
from datetime import datetime, timedelta

# url = 'http://127.0.0.1:5000/orders'
# data = {
#     "address": "富强100发发",
#     "content": "[2,4-3,9-8]",
#     "printer": "杨 Doe",
# }
#
# response = requests.post(url, json=data)
# print(response.text)

now = datetime.now()
time_stamp_30_seconds_ago_in_millis = int((now.timestamp() - 30) * 1000)
print(time_stamp_30_seconds_ago_in_millis)



