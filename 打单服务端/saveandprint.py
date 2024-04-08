import json
import requests
def get_tenant_access_token(app_id, app_secret):
    url_tat = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    post_data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    r = requests.post(url_tat, data=post_data)
    return r.json()["tenant_access_token"]

def read_records(access_token):
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url_read = "https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/tblBmGg1sYkSV9GC/records/search"
    data_read = {}
    r_read = requests.post(url_read, headers=header, json=data_read)
    return r_read.json()

def write_record(access_token, record_data):
    url_write = "https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/tblBmGg1sYkSV9GC/records"
    header = {
        "content-type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    r_write = requests.post(url_write, headers=header, json=record_data)
    return r_write.json()

def main():
    # 获取tenant_access_token
    app_id = "cli_a57140de9afb5013"
    app_secret = "tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs"
    tenant_access_token = get_tenant_access_token(app_id, app_secret)

    while True:
        name = input("输入：")
        print(f"你好，{name}！")

        # 读取电子表格单元格的数据
        records = read_records(tenant_access_token)
        print(records)

        # 写入多维表格一条数据
        new_record_data = {
            "fields": {
                "创单人员": "小明",
                "当前进度": "送货",
                "地址": "富强3号",
                "货物": "[usax],[68:87,99:90,1:1],[]",
                "总体进度": "[出货,2024-12-12 12:00:00,小明],[进货,2024-12-12 12:00:00,小明]"
            }
        }
        write_response = write_record(tenant_access_token, new_record_data)
        print(write_response)

if __name__ == "__main__":
    main()