import pymysql
import os

def insert_data_to_db(collector_id: str, type:str , unit:str ,collected_data: float, collected_time: str):
    # 连接数据库
    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password='password', database='boiler')
        cursor = conn.cursor()
    except pymysql.Error:
        # 如果连接不上数据库，创建一个记事本，将数据写入txt
        with open('data.txt', 'a') as f:
            f.write(f"{collector_id}\t{type}\t{unit}\t{collected_data}\t{collected_time}\n")
        return

    # 如果连接上了数据库
    # 先判断有没有txt，如果有，从txt中读取所有数据写入数据库并删除txt
    if os.path.isfile('data.txt'):
        with open('data.txt', 'r') as f:
            for line in f:
                collector_id, type, unit, collected_data, collected_time = line.strip().split('\t')
                cursor.execute("INSERT INTO data_table (采集器id, 气体类型, 单位, 设备数据, 采集时间) VALUES (%s, %s, %s, %s, %s)",
                               (collector_id, type, unit, collected_data, collected_time))
                conn.commit()
        os.remove('data.txt')

    # 将数据直接写进数据库
    cursor.execute("INSERT INTO data_table (采集器id, 气体类型, 单位, 设备数据, 采集时间) VALUES (%s, %s, %s, %s, %s)",(collector_id, type, unit, collected_data, collected_time))
    conn.commit()

    cursor.close()
    conn.close()
