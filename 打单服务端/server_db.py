from flask import g
import sqlite3
from datetime import datetime

import constants

DATABASE = 'yl.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def insert_record(db, data):
    cur = db.cursor()
    cur.execute('''INSERT INTO orders (
 address, content, cur_status, printer, print_time,
 order_trace, sync_status
 ) VALUES (?,?,?, ?, ?, ?, ?)''', (
        data.get('address'),
        data.get('content'),
        '打单',
        data.get('printer'),
        data.get('print_time'),
        data.get('order_trace'),
        constants.LOCAL_DATA_INIT
    ))
    return cur.lastrowid


def generate_and_update_order_id(db, record_id):
    date_str = datetime.now().strftime('%Y%m%d')
    order_id_str = f"{date_str}{record_id:06}"
    order_id = int(order_id_str)
    print(order_id)
    db.execute("UPDATE orders SET order_id = ? WHERE id = ?", (order_id, record_id))
    return order_id


def get_order_by_id(order_id):
    db = get_db()
    cur = db.cursor()
    order_cursor = cur.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order = order_cursor.fetchone()
    return order

def get_orders(limit, offset):
    # 计算分页
    query = """
        SELECT id, order_id, address, content, cur_status, cur_man, cur_time, printer, print_time, order_trace, update_time, sync_status
        FROM orders
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, (limit, offset))

    # 取出查询结果
    orders = cursor.fetchall()

    # 格式化输出结果
    result = []
    for order in orders:
        result.append({
            'id': order[0],
            'order_id': order[1],
            'address': order[2],
            'content': order[3],
            'cur_status': order[4],
            'cur_man': order[5],
            'cur_time': order[6],
            'printer': order[7],
            'print_time': order[8],
            'order_trace': order[9],
            'update_time': order[10],
            'sync_status': order[11],
        })
    return result


def get_order_ids_by_status(db, status, print_time_before, print_time_after):
    cur = db.cursor()
    sql = """SELECT order_id FROM orders WHERE sync_status = ? AND print_time > ? AND print_time < ?"""
    # 执行查询操作
    cur.execute(sql, (status, print_time_before, print_time_after))
    # 使用列表推导式获取整数型 order_id 列表
    order_ids = [int(order_id["order_id"]) for order_id in cur.fetchall()]
    db.commit()
    return order_ids


def update_order(db, cur_status, cur_man, cur_time, order_trace, sync_status, order_id):
    # 更新本地数据库中的订单数据
    cursor = db.cursor()
    cursor.execute('''UPDATE orders SET cur_status = ?, cur_man = ?, cur_time = ?, order_trace = ?, sync_status = ?
 WHERE order_id = ?''', (cur_status, cur_man, cur_time, order_trace, sync_status, order_id))
    db.commit()
    # 检查更新的行数
    if cursor.rowcount > 0:
        # 如果影响的行数大于零，认为更新成功
        return True
    else:
        # 没有行被更新，可能是因为指定的order_id不存在
        return False


def update_order_status(db, sync_status, order_id):
    cursor = db.cursor()
    # 更新本地数据库中的订单数据
    cursor.execute('''UPDATE orders SET sync_status = ? WHERE order_id = ?''', (sync_status, order_id))
    db.commit()
    # 检查更新的行数
    if cursor.rowcount > 0:
        # 如果影响的行数大于零，认为更新成功
        return 1
    else:
        # 没有行被更新，可能是因为指定的order_id不存在
        return -1


def start_job(db):
    cursor = db.cursor()
    # 尝试更新job状态
    cursor.execute("UPDATE job SET job_status = 1 WHERE job_status = 0 AND id = 1")
    # 检查是否更新成功
    if cursor.rowcount == 1:
        db.commit()
        print("Job started successfully.")
        return True
    else:
        print("Another job is already running.")
        return False


def finish_job(db):
    cursor = db.cursor()
    # 完成job，将状态更新回0
    cursor.execute("UPDATE job SET job_status = 0 WHERE id = 1")
    db.commit()
    print("Job finished.")


def init_db():
    print("init db")
    db = get_db()
    # 订单表结构
    # id INTEGER PRIMARY KEY, 订单自增id，如1,2
    # 如打单（printer）、配货（picker）、送货（deliveryman）、对接（coordinator）、对接送货（receiver）
    # cur_status TEXT, 订单当前状态，
    # cur_man TEXT, 当前处理人
    # cur_time DATETIME, 当前处理时间
    # order_id INTEGER, 订单编号，如20240311000001
    # address TEXT, 订单地址
    # content TEXT, 订单内容 包含规格、长度-条数、备注
    # printer TEXT, 打单人
    # print_time DATETIME, 打单时间
    # order_trace TEXT,订单轨迹
    # sync_status INTEGER 订单同步状态 0表示初始化；100表示此订单完结，后续无需同步

    # update_time 更新时间
    # db.execute("DROP TABLE IF EXISTS orders")
    db.execute(
        '''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY, 
        order_id INTEGER,
        address TEXT,
        content TEXT,
        
        cur_status TEXT, 
        cur_man TEXT, 
        cur_time DATETIME, 
    
        printer TEXT,
        print_time TIMESTAMP,
       
        order_trace TEXT,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sync_status INTEGER)''')
    # job_status INTEGER job更新状态 同一时刻只有一个job在串行跑 0表示没有跑 1表示正在跑
    db.execute(
        '''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY, 
        job_type TEXT NOT NULL,
        job_status INTEGER,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 为order_id列创建索引
    db.execute('''CREATE INDEX IF NOT EXISTS idx_order_id ON orders (order_id)''')
    db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_job_type ON jobs (job_type)''')

    # 初始化 其他地方不得用Insert
    job_types = [constants.JOB_ONE, constants.JOB_TWO]
    init_job_trans(db, job_types)
    db.commit()
    return "Database initialized."


def init_job_trans(db, job_types):
    cursor = db.cursor()
    for job_type in job_types:
        cursor.execute("INSERT INTO jobs (job_type, job_status) VALUES (?, 0)", (job_type,))
    db.commit()


def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
