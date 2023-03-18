import pymysql
import os

def insert_data_to_db(collector_id: int, collected_data: float, collected_time: str):
    # Set up MySQL connection
    try:
        conn = pymysql.connect(host='133.0.0.2', user='root', password='password', database='boiler')
    except:
        # If connection fails, write data to text file
        with open('data.txt', 'a') as f:
            f.write(f"{collector_id}\t{collected_data}\t{collected_time}\n")
        return

    # If connection succeeds, insert data into MySQL
    try:
        with conn.cursor() as cursor:
            # Retrieve all data from table
            cursor.execute("SELECT * FROM data_table")
            rows = cursor.fetchall()

            # Insert new data into table
            cursor.execute("INSERT INTO data_table (采集器id, 设备数据, 采集时间) VALUES (%s, %s, %s)",
                           (collector_id, collected_data, collected_time))
            conn.commit()

            # Delete text file if it exists
            if os.path.exists('data.txt'):
                os.remove('data.txt')
    finally:
        conn.close()
insert_data_to_db(1,4.43,'2023-03-18 10:00:06')
insert_data_to_db(1,4.43,'2023-03-18 10:00:07')
