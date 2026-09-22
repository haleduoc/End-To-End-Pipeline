# Kiểm tra đã load được vào DB chưa
import os
import pymysql
from dotenv import load_dotenv

BASE_ENV = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_ENV, ".env"))

conn = pymysql.connect(
    host=os.getenv("mysql_host"), port=int(os.getenv("mysql_port")),
    user=os.getenv("mysql_user"), password=os.getenv("mysql_password"),
    database=os.getenv("mysql_database"), cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) AS TOTAL FROM raw_tiki_products;")
    print(f"Tổng số dòng đã load:", cur.fetchone())

    cur.execute("SELECT product_id, name, price, extracted_at FROM raw_tiki_products LIMIT 3;")
    for row in cur.fetchall():
        print(row)
conn.close()