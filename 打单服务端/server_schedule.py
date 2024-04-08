import requests
import server_db
import sqlite3
import server_feishu
import time
from datetime import datetime, timedelta
import constants
from flask import current_app as app


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

    sync0_order_ids = set(get_order_ids_from_feishu(order_ids))

    difference = list(set(order_ids) - sync0_order_ids)

    app.logger.info(
        "scheduled_job1_insert_feishu job need insert " + str(difference) + " need set sync = 1 ," + str(
            sync0_order_ids))

    for order_id in sync0_order_ids:
        server_db.update_order_status(db, constants.LOCAL_DATA_FIRST_INSERT, order_id)

    # insert
    for order_id in difference:
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

        server_feishu.write_one_record(new_record_data)
        time.sleep(1)
    app.logger.info("end scheduled_job1_insert_feishu job....................")


def get_order_ids_from_feishu(initial_order_id):
    # 假定 read_records_by_Ids 已正确实现并返回数据
    if not initial_order_id:
        return []
    response_data = server_feishu.read_records_by_order_ids(initial_order_id)
    if response_data['code'] == 0:
        order_ids = [item['fields']['订单编号'] for item in response_data['data']['items']]
    else:
        app.logger.info("Error in fetching records")
        return []
    return order_ids


# todo 将打单时间>14天 且 当前状态为 发货 的单子 从feishu中删除 删除前把这份数据同步到本地服务器
def scheduled_job2_delete_feishu_update_local(db):
    app.logger.info("start scheduled_job2_delete_feishu_update_local job................")
    has_more = True
    # 以下是处理订单的代码
    try:
        # 读取远程web服务获取数据
        while has_more:
            response = server_feishu.read_records()
            if response["code"] == 0:
                orders = response["data"]["items"]
                has_more = response["data"]["has_more"]
                app.logger.info("Scheduled job need process orders " + str(orders))
                # 更新数据库和删除远程数据
                process_orders(db, orders)
                app.logger.info("Scheduled job completed successfully")
            else:
                # todo 处理异常 如果是false此次更新就失败了
                has_more = False
            app.logger.info("Remote service call success with status code:", response["code"])
    except requests.HTTPError as e:
        app.logger.info(f"An HTTP error occurred: {e}")
    except sqlite3.Error as e:
        app.logger.info(f"Database error: {e}")
    except Exception as e:
        app.logger.info(f"An error occurred: {e}")

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
        status = constants.LOCAL_DATA_FIRST_INSERT

        if cur_status == constants.DELIVERY:
            status = constants.REMOTE_DATA_CAN_BE_DELETE

        # 创建时间超过一定的天数订单且状态是送货中 从远程删除掉
        if is_timestamp_older_than_x_days(creation_time, constants.OLD_DATA_DAY):
            if cur_status == constants.DELIVERY:
                status = constants.REMOTE_DATA_TO_BE_DELETE
                orders_to_delete.append(record_id)
        server_db.update_order(db, cur_status, cur_man, cur_time, order_trace, status, order_id)

    # end for
    app.logger.info(f"begin delete orders {orders_to_delete} from remote service")
    server_feishu.delete_records(orders_to_delete)
    app.logger.info(f"end delete orders {orders_to_delete} from remote service")


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
