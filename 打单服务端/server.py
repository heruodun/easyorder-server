import logging
import os
import sys
import threading
from logging.handlers import TimedRotatingFileHandler

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from flask import Flask, request, g, jsonify, current_app
import time
import constants
import server_db
import server_feishu
import sqlite3
import server_schedule
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
version = "1.0.0"


def init_logger():
    # 获取exe文件（或脚本）的当前路径
    if getattr(sys, 'frozen', False):
        # 如果程序是"冻结"状态（即被编译为exe），使用这种方式
        application_path = os.path.dirname(sys.executable)
    else:
        # 否则就是普通的Python脚本运行
        application_path = os.path.dirname(os.path.abspath(__file__))

    # 定义日志文件的路径（放在exe文件/脚本所在目录的logs子目录下）
    log_directory = os.path.join(application_path, 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)  # 如果logs目录不存在，则创建之

    log_file_path = os.path.join(log_directory, 'server_app.log')

    # 设置日志记录器
    handler = TimedRotatingFileHandler(log_file_path, when='midnight', backupCount=100)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(threadName)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    # 将日志处理器添加到 Flask 的默认日志记录器中
    app.logger.addHandler(handler)

    # 设置日志记录级别
    app.logger.setLevel(logging.INFO)


# 记录所有请求的信息（可选）
@app.before_request
def before_request_logging():
    app.logger.info("Received request: %s %s", request.method, request.url)


#
#
# 记录所有响应的信息（可选）
@app.after_request
def after_request_logging(response):
    app.logger.info("Sending response: %s - %s", response.status, response.data)
    return response


def index():
    # 使用HTML的<style>来设置文本样式
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>''' + constants.COMPANY_NAME + '''打单服务''' + version + '''</title>
        <style>
            body, html {
                height: 100%;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .welcome {
                color: red;
                font-weight: bold;
                font-size:50px;
            }
        </style>
    </head>
    <body>
        <div class="welcome">欢迎来到''' + constants.COMPANY_NAME + '''打单服务!</div>
    </body>
    </html>
    '''


def call_remote_service_async(insert_data, msg_data, order_id):
    app.logger.info("call_remote_service_async begin to insert one order to feishu async %s", insert_data)
    app.logger.info("call_remote_service_async begin to send one msg to feishu async %s", msg_data)
    count = 0
    ok = False

    while not ok and count < 3:  # 使用while循环重试逻辑
        ok = server_feishu.write_one_record(insert_data)
        if ok:
            app.logger.info("call_remote_service_async insert one order to feishu async success %s", order_id)
            with app.app_context():
                db = server_db.get_db();
                server_db.update_order_status(db, constants.LOCAL_DATA_FIRST_INSERT, order_id)
                app.logger.info("call_remote_service_async update one order sync status to 1 success %s", order_id)
            server_feishu.send_one_message(msg_data)
        if not ok:
            # 如果请求没有成功，稍微等待一段时间再次重试
            time.sleep(1)  # 等待1秒再次尝试
    if not ok:
        # 这里处理所有尝试失败的逻辑，如记录日志或发送报警通知
        app.logger.error("Insert one order to feishu async %s times fail %s", count, insert_data)


def get_str_from_excel(excel_str):
    result_str = ""
    if excel_str is not None:
        result_str = str(excel_str).strip()
    return result_str


def order_post_data1(A12_H26):
    # 地址数据
    dizhi = A12_H26[0][1]
    # 创单人员
    man = A12_H26[14][1]
    # 总条数
    total_count = A12_H26[12][1]
    # 长度数据
    # 条数数据

    str_l_d = ""
    # 规格数据
    guige = ""
    # 备注数据
    beizhu = ""
    for i in range(0, 9):
        length = get_str_from_excel(A12_H26[i + 3][2])
        count = get_str_from_excel(A12_H26[i + 3][4])
        guige = guige + get_str_from_excel(A12_H26[i + 3][0])
        beizhu = beizhu + get_str_from_excel(A12_H26[i + 3][5])

        # 如果两个都为空，则跳过当前循环
        if length == "" and count == "":
            continue
        # 如果length为空，则将length置为0
        if length == "":
            length = 0
        # 如果count为空，则将count置为0
        if count == "":
            count = 0



        # 如果length是整数，则去掉小数部分
        if isinstance(length, float) and length.is_integer():
            length_str = str(int(length))
        else:
            length_str = str(length)

        # 如果count是整数，则去掉小数部分
        if isinstance(count, float) and count.is_integer():
            count_str = str(int(count))
        else:
            count_str = str(count)
        str_l_d += length_str + " x " + count_str + "，"
    str_l_d = str_l_d[:-1]

    # 如果total_count是整数，则去掉小数部分
    if isinstance(total_count, float) and total_count.is_integer():
        total_count_str = str(int(total_count))
    else:
        total_count_str = str(total_count)

    if man is None:
        man = ""
    if dizhi is None:
        dizhi = ""
    if guige is None:
        guige = ""
    if total_count_str is None:
        total_count_str = ""
    if beizhu is None:
        beizhu = ""

    new_record_data = {
        "printer": man,
        "address": dizhi,
        "content": "规格：" + str(
            guige) + "\n\n长度和条数：" + str_l_d + "\n\n总条数：" + total_count_str + "\n\n备注：" + str(beizhu)
    }
    return new_record_data


def order_post_data2(A12_H26):
    # 地址数据
    dizhi = A12_H26[0][1]
    # 创单人员
    man = A12_H26[14][1]
    # 规格 * 数量 单位
    str_g_l_d = "规格和数量："
    # 备注数据
    beizhu = get_str_from_excel(A12_H26[9][1])

    for i in range(0, 4):
        guige = get_str_from_excel(A12_H26[i + 3][1])
        count = get_str_from_excel(A12_H26[i + 3][4])
        danwei = get_str_from_excel(A12_H26[i + 3][6])

        # 如果两个都为空，则跳过当前循环
        if guige == "" and count == "":
            continue

        # 如果count为空，则将count置为0
        if count == "":
            count = 0
        str_g_l_d += guige + " X " + str(count) + " " + danwei + "，"
    str_g_l_d = str_g_l_d[:-1]

    if man is None:
        man = ""
    if dizhi is None:
        dizhi = ""
    if beizhu is None:
        beizhu = ""

    new_record_data = {
        "printer": man,
        "address": dizhi,
        "content": str_g_l_d + "\n\n备注：" + str(beizhu)
    }
    return new_record_data


def save_one_order(data):
    if not data:
        return jsonify({"error": "Missing data in JSON payload"}), 400
    db = server_db.get_db()
    try:
        current_timestamp = time.time()
        timestamp_ms = int(current_timestamp * 1000)
        data["print_time"] = timestamp_ms

        # 将时间戳转换为本地时间的 struct_time 对象
        local_time = time.localtime(current_timestamp)
        # 将 struct_time 对象格式化为字符串
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        data["order_trace"] = "打单人：" + data["printer"] + "，" + "打单时间：" + formatted_time
        record_id = server_db.insert_record(db, data)
        order_id = server_db.generate_and_update_order_id(db, record_id)
        db.commit()

        new_record_data = {
            "fields": {
                "订单编号": order_id,
                "编号": record_id,
                "地址": data["address"],
                "货物": data["content"],
                "打单时间": timestamp_ms,
                "打单人": data["printer"],
                "当前进度": constants.PRINT,
                "当前处理人": data["printer"],
                "当前处理时间": timestamp_ms,
                "总体进度": "打单人：" + data["printer"] + "，打单时间：" + formatted_time
            }
        }

        new_msg_data = {
            "order_id": order_id,
            "id": record_id,
            "address": data["address"],
            "content": data["content"],
            "cur_progress": constants.PRINT,
            "cur_man": data["printer"],
            "cur_time": formatted_time
        }
        a
        thread = threading.Thread(target=call_remote_service_async, args=(new_record_data, new_msg_data, order_id, ))
        thread.start()

        return jsonify({
            "status": "Order added and updated",
            "record_id": record_id,
            "order_id": order_id,
            "qr_code": str(order_id) + "$xiaowangniujin",
            "create_time": formatted_time
        }), 201
    except sqlite3.Error as e:
        app.logger.error("Insert one order to local sync fail %s", data, e)
        return jsonify({"error": str(e)}), 500


def order1():
    if request.method == 'POST':
        a12_f26 = request.get_json()["data"]
        data = order_post_data1(a12_f26)
        return save_one_order(data)
    return jsonify({"error": "no method"}), 400


def orders():
    if request.method == 'POST':
        a12_f26 = request.get_json()["data"]
        data = order_post_data1(a12_f26)
        return save_one_order(data)
    return jsonify({"error": "no method"}), 400


def order2():
    if request.method == 'POST':
        a12_f26 = request.get_json()["data"]
        data = order_post_data2(a12_f26)
        return save_one_order(data)
    return jsonify({"error": "no method"}), 400


def get_order_by_id():
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({"error": "Missing 'order_id' in query parameters"}), 400
    order = server_db.get_order_by_id(order_id)
    if order:
        return jsonify(dict(order)), 200
    else:
        return jsonify({"error": "Order not found"}), 404


def init_db():
    server_db.init_db()
    return "Database initialized."


def login():
    phone = request.args.get('phone')
    password = request.args.get('password')
    if not phone:
        return jsonify({"error": "Missing 'phone' in query parameters"}), 400
    if not password:
        return jsonify({"error": "Missing 'password' in query parameters"}), 400

    code, name = server_feishu.read_users(phone, password)

    if code == 0:
        if name is not None:
            return name, 200
        else:
            return jsonify({"error": "user not found"}), 404
    else:
        return jsonify({"error": "user not found"}), 500


def sync_data1():
    scheduled_job1_30_d_local()
    return jsonify({"local job run": "ok"}), 200


def sync_data2():
    scheduled_job2_14_d_remote_job()
    return jsonify({"remote job run": "ok"}), 200


# 注册路由
app.add_url_rule('/', 'index', index)
# 创建模板一的一个订单
app.add_url_rule('/order1', 'order1', order1, methods=['POST'])

app.add_url_rule('/orders', 'orders', orders, methods=['POST'])
# 创建模板二的一个订单
app.add_url_rule('/order2', 'order2', order2, methods=['POST'])
# 获取一个订单
app.add_url_rule('/order', 'get_order_by_id', get_order_by_id, methods=['GET'])
# 初始化数据库
app.add_url_rule('/initdb', 'init_db', init_db, methods=['GET'])
# 用户登录
app.add_url_rule('/login', 'login', login, methods=['GET'])

app.add_url_rule('/sync1', 'sync1', sync_data1, methods=['GET'])

app.add_url_rule('/sync2', 'sync2', sync_data2, methods=['GET'])

# 注册应用上下文的清理函数
app.teardown_appcontext(server_db.close_connection)


# 30天内本地创建的单子且未被同步到feishu
def scheduled_job1_30_d_local():
    with app.app_context():
        db = server_db.get_db()
        server_schedule.execute_job_without_transaction(db, constants.JOB_ONE)


def scheduled_job2_14_d_remote_job():
    with app.app_context():
        db = server_db.get_db()
        server_schedule.execute_job_without_transaction(db, constants.JOB_TWO)


def init_job():
    # 初始化定时任务
    scheduler = BackgroundScheduler()
    # 每天凌晨2点执行
    scheduler.add_job(scheduled_job2_14_d_remote_job, 'cron', hour=2, minute=0)
    # 每隔5分钟一次
    scheduler.add_job(scheduled_job1_30_d_local, 'interval', minutes=2)
    scheduler.start()


def start_flask_app():
    # 在应用启动时立即初始化数据库（通过访问/initdb路由）
    init_job()
    init_logger()
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)


def main():
    server_env = os.getenv(constants.SERVER_ENV_KEY)
    if server_env is None:
        # sys.exit("错误：环境变量 " + constants.SERVER_ENV_KEY + " 未配置，请设置后再运行程序。")
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "环境变量错误",
                             "错误：环境变量 " + constants.SERVER_ENV_KEY + " 未配置，请设置后再运行程序。")
        sys.exit(1)

    app = QApplication([])
    # 获取当前文件夹的路径
    current_dir = os.path.dirname(os.path.realpath(__file__))
    # 构建图标的完整路径
    icon_path = os.path.join(current_dir, "icon.png")
    tray_icon = QSystemTrayIcon(QIcon(icon_path), app)
    tray_icon.setToolTip(constants.COMPANY_NAME + "打单服务")
    menu = QMenu()
    exit_action = menu.addAction("退出")
    tray_icon.setContextMenu(menu)
    exit_action.triggered.connect(app.quit)
    tray_icon.show()

    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
