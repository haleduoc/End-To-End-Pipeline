# Step 2: Connect server mysql
import os
import pymysql
from dotenv import load_dotenv

# Nạp toàn bộ biến trong .env để connect MYSQL
load_dotenv()

try:
    conn = pymysql.connect(
        host=os.getenv("mysql_host"),
        port=int(os.getenv("mysql_port")),
        user=os.getenv("mysql_user"),
        password=os.getenv("mysql_password"),
        database=os.getenv("mysql_database"),
        connect_timeout=10
)
    print("Kết nối MYSQL thành công")
    conn.close() # Đóng kết nối tránh lãng phí tài nguyên server
except Exception as e:
    print(f"Lỗi {e}")