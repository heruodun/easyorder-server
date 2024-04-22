import logging

import requests
import server_db
import sqlite3
import server_feishu
import time
from datetime import datetime, timedelta
import constants
from flask import current_app as app, g


def execute_job_without_transaction(db, job_type):
    # 任务启动，此时job_status已经被更新为1
    # 执行任务
    if job_type == constants.JOB_ONE:
        scheduled_job1_insert_feishu(db)

    if job_type == constants.JOB_TWO:
        scheduled_job2_delete_feishu_update_local(db)


def execute_job_with_transaction(db, job_type):
    try:
        db.execute("BEGIN")
        # 通过UPDATE语句的行为来试图“锁定”任务
        cursor = db.execute("UPDATE jobs SET job_status = 1 WHERE job_type = ? AND job_status = 0", (job_type,))
        if cursor.rowcount == 0:
            # 如果没有行被更新，那么任务可能已经在运行
            app.logger.info(f"Job {job_type} is already running.")
            db.rollback()  # 回滚以释放任何可能的锁
            return

        # 任务启动，此时job_status已经被更新为1
        # 执行任务
        if job_type == constants.JOB_ONE:
            scheduled_job1_insert_feishu(db)

        if job_type == constants.JOB_TWO:
            scheduled_job2_delete_feishu_update_local(db)

        # 任务完成，更新状态为未运行
        db.execute("UPDATE jobs SET job_status = 0 WHERE job_type = ? AND job_status = 1", (job_type,))

        db.commit()
    except Exception as e:
        db.rollback()
        app.logger.error(f"Error during {job_type} job execution: {e}")
    finally:
        db.close()


def separate_order_id_lists(order_ids, existence_list):
    # 列表初始化
    existing_orders = []
    non_existing_orders = []
    failed_orders = []

    # 根据存在性列表对订单ID进行分类
    for i, status in enumerate(existence_list):
        if status == 1:
            existing_orders.append(order_ids[i])
        elif status == 0:
            non_existing_orders.append(order_ids[i])
        elif status == -1:
            failed_orders.append(order_ids[i])

    return existing_orders, non_existing_orders, failed_orders


def scheduled_job1_insert_feishu(db):
    app.logger.info("start scheduled_job1_insert_feishu job....................")
    now = datetime.now()
    # db = server_db.get_db()
    # 计算现在时间往前30天的时间点
    thirty_days_ago = now - timedelta(days=30)

    # 将时间转换为毫秒时间戳
    # datetime.timestamp() 返回的是秒为单位的时间戳，所以乘以1000转换为毫秒，并将结果转换成整数
    time_stamp_30_days_ago_in_millis = int(thirty_days_ago.timestamp() * 1000)

    # 30秒前的毫秒时间戳 因为要避免和插入操作同时插入到飞书
    time_stamp_30_seconds_ago_in_millis = int((now.timestamp() - 30) * 1000)

    order_ids = server_db.get_order_ids_by_status(db, constants.LOCAL_DATA_INIT, time_stamp_30_days_ago_in_millis
                                                  , time_stamp_30_seconds_ago_in_millis)

    app.logger.info("scheduled_job1_insert_feishu job sync = 0 ," + str(order_ids))

    existing, non_existing, failed = find_order_exist_from_feishu(order_ids)

    app.logger.info(
        "scheduled_job1_insert_feishu job, " + str(non_existing) + " need insert to feishu")
    app.logger.info(
        "scheduled_job1_insert_feishu job, " + str(existing) + " need update local sync = 1")

    for order_id in existing:
        server_db.update_order_status(db, constants.LOCAL_DATA_FIRST_INSERT, order_id)

    # insert
    for order_id in non_existing:
        order = server_db.get_order_by_id(order_id)
        new_record_data = {
            "fields": {
                "订单编号": order_id,
                "编号": order["id"],
                "地址": order["address"],
                "货物": order["content"],
                "打单时间": order["print_time"],
                "打单人": order["printer"],
                "当前进度": constants.PRINT,
                "当前处理人": order["printer"],
                "当前处理时间": order["print_time"],
                "总体进度": order["order_trace"]
            }
        }

        # 因为datetime模块处理的是秒时间戳，所以需要将毫秒时间戳转换成秒
        seconds_timestamp = order["print_time"] / 1000

        # 使用`fromtimestamp`函数来创建一个datetime对象
        dt_object = datetime.fromtimestamp(seconds_timestamp)

        # 将datetime对象格式化为字符串
        formatted_date_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        new_msg_data = {
            "order_id": order_id,
            "id": order["id"],
            "address": order["address"],
            "content": order["content"],
            "cur_progress": constants.PRINT,
            "cur_man": order["printer"],
            "cur_time": formatted_date_str
        }
        ok = server_feishu.write_one_record(new_record_data)
        if ok:
            server_db.update_order_status(db, constants.LOCAL_DATA_FIRST_INSERT, order_id)
            server_feishu.send_one_message(new_msg_data)
        time.sleep(1)
    app.logger.info("end scheduled_job1_insert_feishu job....................")


# 查询feishu中是否有该订单id，1存在，0不存在，-1异常
def find_order_exist_from_feishu(order_ids):
    # 若输入为空，返回空列表
    if not order_ids:
        return [], [], []

    # 设置每次请求的订单 ID 数量
    page_size = 20
    existing_orders = []
    non_existing_orders = []
    failed_orders = []

    # 将订单 ID 拆分为每 page_size 个一组进行查询
    for start_index in range(0, len(order_ids), page_size):
        ids_batch = order_ids[start_index:start_index + page_size]
        try:
            response_data = server_feishu.read_records_by_order_ids(ids_batch)
            if response_data['code'] == 0:
                # 若成功获取响应，遍历 response_data 获取每个订单ID的存在性
                existing_order_ids = {item['fields']['订单编号'] for item in response_data['data']['items']}
                for order_id in ids_batch:
                    if order_id in existing_order_ids:
                        existing_orders.append(order_id)
                    else:
                        non_existing_orders.append(order_id)
            else:
                app.logger.error("Error in fetching records from feishu: %s", response_data)
                failed_orders.extend(ids_batch)  # 处理失败，认为本批次所有订单查询都失败
                break  # 这里选择中断所有批次的查询，也可以选择注释掉继续查询

        except Exception as e:
            app.logger.error("Exception occurred while fetching records: %s", e)
            failed_orders.extend(ids_batch)  # 查询出错，认为本批次所有订单查询都失败

    return existing_orders, non_existing_orders, failed_orders


# todo 将打单时间>14天 且 当前状态为 发货 的单子 从feishu中删除 删除前把这份数据同步到本地服务器
def scheduled_job2_delete_feishu_update_local(db):
    app.logger.info("start scheduled_job2_delete_feishu_update_local job................")
    has_more = True
    page_token = None
    page_size = 20
    # 以下是处理订单的代码
    try:
        # 读取远程web服务获取数据
        while has_more:
            response = server_feishu.read_records(page_token, page_size)
            if response["code"] == 0:
                orders = response["data"]["items"]
                has_more = response["data"]["has_more"]
                app.logger.info("Scheduled job need process orders " + str(orders))
                # 更新数据库和删除远程数据
                process_orders(db, orders)
                if has_more:
                    page_token = response["data"]["page_token"]
                else:
                    page_token = None
            else:
                has_more = False
            app.logger.info("Remote service call success with status code: %s", response["code"])
    except requests.HTTPError as e:
        app.logger.error(f"An HTTP error occurred: {e}")
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")

    app.logger.info("end scheduled_job2_delete_feishu_update_local job................")


def process_orders(db, orders):
    orders_to_delete = []  # 用于收集需要从远程服务中删除的订单
    for order in orders:
        creation_time = order["fields"]["打单时间"]
        cur_time = order["fields"]["当前处理时间"]
        cur_status = order["fields"]["当前进度"]
        cur_man = order["fields"]["当前处理人"][0]["text"]
        order_trace = order["fields"]["总体进度"][0]["text"]
        order_id = order["fields"]["订单编号"]
        record_id = order["record_id"]
        # update local data
        # process local data sync status
        status = constants.REMOTE_DATA_UPDATE_LOCAL

        if cur_status == constants.DELIVERY:
            status = constants.REMOTE_DATA_CAN_BE_DELETE

        # 创建时间超过一定的天数订单且状态是送货中 从远程删除掉
        if is_timestamp_older_than_x_days(creation_time, constants.DONE_DELETE_DATA_DAY):
            if (cur_status == constants.DELIVERY) or (cur_status == constants.RECEIVE):
                status = constants.REMOTE_DATA_TO_BE_DELETE

        if is_timestamp_older_than_x_days(creation_time, constants.ALL_DELETE_DATA_DAY):
            status = constants.REMOTE_DATA_TO_BE_DELETE

        # update local data
        ok = server_db.update_order(db, cur_status, cur_man, cur_time, order_trace, status, order_id)
        if ok and (status == constants.REMOTE_DATA_TO_BE_DELETE):
            orders_to_delete.append(record_id)

    # end for
    if orders_to_delete:
        app.logger.info(f"begin delete orders > 14 days or > 30days  {orders_to_delete} from remote service")
        server_feishu.delete_records_in_batches(orders_to_delete, 200)
        app.logger.info(f"end delete orders > 14 days or > 30days {orders_to_delete} from remote service")
    else:
        app.logger.info(f"orders > 14 days or > 30days is none from remote service")


def is_timestamp_older_than_x_days(timestamp_ms, x_days):
    """
    检查毫秒级时间戳是否比当前时间小x天

    :param timestamp_ms: 毫秒级时间戳
    :param x_days: 天数
    :return: 如果时间戳比当前时间小x天，则返回True，否则返回False
    """
    # 将毫秒级时间戳转换成秒
    timestamp_s = timestamp_ms / 1000.0
    # 将时间戳转换成datetime对象
    timestamp_date = datetime.fromtimestamp(timestamp_s)

    # 获取当前时间
    current_date = datetime.now()

    # 计算x天前的日期
    x_days_ago = current_date - timedelta(days=x_days)

    # 比较
    return timestamp_date < x_days_ago


def scheduled_job3_update_local_addresses_job(db):
    addresses = server_feishu.read_all_addresses()
    code = server_db.insert_or_update_addresses(db, addresses)
    if code == 0:
        addresses = server_db.get_addresses()
        place_list = [item['place'] for item in addresses]
        place_list.sort(key=constants.sort_key)
        app.config['places'] = place_list
        logging.info("scheduled_job3_update_local_addresses_job update success")
    else:
        logging.error("scheduled_job3_update_local_addresses_job update fail")
