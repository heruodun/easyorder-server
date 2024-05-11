import logging

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


def query_addresses_by_ids(ids=None):
    query = """
        SELECT id, place, coordinate
        FROM addresses
    """
    if ids:
        query += " WHERE id IN ({})".format(", ".join(["?"] * len(ids)))
    db = get_db()

    logging.info(str(query))
    logging.info(str(ids))

    cursor = db.cursor()
    cursor.execute(query, ids if ids else ())
    logging.info(str("execute"))
    items = cursor.fetchall()
    logging.info(str("fetchall"))

    result = []
    for index, item in enumerate(items):
        id_, place, coordinate = item

        # 检查coordinate是否包含逗号，以分割为longitude和latitude；
        # 如果不符合预期，可以设置默认值或进行其他处理
        if ',' in coordinate:
            longitude, latitude = coordinate.split(',')
        else:
            # 定义一种错误处理方式，例如使用默认值
            longitude, latitude = '0', '0'  # 或使用None, None等

        result.append((index, float(longitude), float(latitude), id_, place))
    return result


def query_all_valid_addresses():
    # 计算分页
    query = """
        SELECT id, place, coordinate
        FROM addresses
        ORDER BY id
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, )

    # 取出查询结果
    items = cursor.fetchall()

    result = []
    index = 0  # 初始化index为0
    for item in items:
        id_, place, coordinate = item
        # 检查coordinate是否包含逗号，以分割为longitude和latitude；
        # 如果不符合预期，可以设置默认值或进行其他处理
        if ',' in coordinate:
            longitude, latitude = coordinate.split(',')
            result.append((index, float(longitude), float(latitude), id_, place))
            index = index + 1  # 如果上述条件成立，则index自增1
    return result


def get_addresses():
    # 计算分页
    query = """
        SELECT id, place, coordinate
        FROM addresses
        ORDER BY id
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, )

    # 取出查询结果
    items = cursor.fetchall()

    # 格式化输出结果
    result = []
    for order in items:
        result.append({
            'id': order[0],
            'place': order[1],
            'coordinate': order[2],
        })
    return result


def insert_or_update_addresses(db_conn, addresses):
    """
    批量插入或更新地址记录。

    参数:
    - db_conn: 数据库连接对象。
    - addresses: 一个列表，其中每个元素包含(id, place, coordinate)。
    """

    # 准备SQL语句，INSERT OR REPLACE 语句会根据记录是否存在(id相同)来决定是插入还是更新
    sql = '''INSERT OR REPLACE INTO addresses (id, place, coordinate) 
             VALUES (?, ?, ?)'''

    # 使用cursor对象执行批量插入或更新操作
    cursor = db_conn.cursor()
    try:
        cursor.executemany(sql, addresses)
        db_conn.commit()  # 提交事务，确保变更保存到数据库
        logging.info(f"{cursor.rowcount} records inserted/updated successfully.")
        return 0
    except sqlite3.Error as e:
        logging.error(f"An error occurred: {e}")
        db_conn.rollback()  # 如果出现错误，回滚事务
        return -1

    cursor.close()


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


def update_order_trace(db, order_trace, order_id):
    # 更新本地数据库中的订单数据
    cursor = db.cursor()
    cursor.execute('''UPDATE orders SET order_trace = ? WHERE order_id = ?''', (order_trace, order_id))
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


def get_orders_by_wave_ids(wave_ids):
    db = get_db()  # 假设这个函数已经定义好，返回数据库连接
    order_map = {}  # <wave_id, order>

    if not wave_ids:
        # 如果 wave_ids 为空，则直接返回空字典
        return order_map

    # 使用tuple(wave_ids)确保参数是一个元组，即使wave_ids只有一个元素
    placeholders = ','.join(['?'] * len(wave_ids))  # 构建所需的SQL参数占位符字符串
    sql = f"SELECT * FROM orders WHERE wave_id IN ({placeholders}) ORDER BY order_id DESC"

    cur = db.cursor()
    cur.execute(sql, tuple(wave_ids))
    print(tuple(wave_ids))
    for order in cur.fetchall():
        wave_id = order['wave_id']  # 假设 order 字典里有 'wave_id' 键
        order_entity = {
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
            'wave_id': order[12],
        }

        if wave_id not in order_map:
            order_map[wave_id] = []
        order_map[wave_id].append(order_entity)  # 将此订单添加到相应 wave_id 的列表中

    cur.close()
    return order_map


def update_order_wave(wave_id, cur_status, cur_time, cur_man, order_trace, order_id):
    db = get_db()
    cur = db.cursor()

    # 准备SQL更新语句
    update_sql = ''' 
    UPDATE orders 
    SET wave_id = ?, 
        cur_status = ?, 
        cur_time = ?, 
        cur_man = ?, 
        order_trace = ?
    WHERE order_id = ?
    '''

    # 执行更新
    try:
        cur.execute(update_sql,
                    (wave_id, cur_status, cur_time, cur_man, order_trace, order_id))
        db.commit()

    except sqlite3.Error as e:
        print(f'Database error: {e}')
        # 在此处处理任何数据库相关的异常
    except Exception as e:
        print(f'Exception in _query: {e}')
        # 在此处处理其他异常
    if cur.rowcount > 0:
        # 如果影响的行数大于零，认为更新成功
        return 1
    else:
        # 没有行被更新，可能是因为指定的order_id不存在
        return -1


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

    db.execute(
        '''CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY, 
        place TEXT NOT NULL,
        coordinate TEXT NOT NULL,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    try:
        db.execute(
            '''
            ALTER TABLE orders ADD COLUMN wave_id INTEGER;
            '''
        )
    except Exception as e:
        print(f'Exception in _query: {e}')

    db.execute('''CREATE INDEX IF NOT EXISTS idx_wave_id ON orders (wave_id)''')

    # 为order_id列创建索引
    db.execute('''CREATE INDEX IF NOT EXISTS idx_order_id ON orders (order_id)''')
    db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_job_type ON jobs (job_type)''')

    # 初始化 其他地方不得用Insert
    # job_types = [constants.JOB_ONE, constants.JOB_TWO]
    # init_job_trans(db, job_types)
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
