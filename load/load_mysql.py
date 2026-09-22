# Trong ELT, tầngd Load sẽ nạp dữ liệu thô nguyên vẹn vào một bảng Raw Table
# Trong DB - chưa lọc, chưa biến đổi gì
# Dùng batch insert để đẩy toàn bộ danh sách sản phẩm trong một lần gọi
# thay vì insert từng dòng, giúp giảm tải đáng kể cho đường truyền lên cloud

from enum import EnumDict
import os
import json
import pymysql
from dotenv import load_dotenv

# Lấy các biến của file .env
BASE_ENV = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_ENV, ".env"))

# connect DB với pymysql
def get_connection():
    return pymysql.connect(
        host=os.getenv("mysql_host"),
        port=int(os.getenv("mysql_port")),
        user=os.getenv("mysql_user"),
        password=os.getenv("mysql_password"),
        database=os.getenv("mysql_database"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# Tạo bảng
def create_table(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS raw_tiki_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT,
    name VARCHAR(500),
    price DECIMAL(15, 2),
    original_price DECIMAL(15, 2),
    discount_rate INT,
    rating_average FLOAT,
    review_count INT,
    seller_name VARCHAR(255),
    extracted_at VARCHAR(100),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("Bảng 'raw_tiki_products' đã sẵn sàng")

# Load data vào bảng đã tạo trong DB
def load_data():
    # Lấy file đường dẫn
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(BASE_DIR, "extract", "data", "raw_product.json")
    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    insert_sql = """
    INSERT INTO raw_tiki_products
        (product_id, name, price, original_price, discount_rate,
        rating_average, review_count, seller_name, extracted_at)
    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    records = [
        (p.get("product_id"), p.get("name"), p.get("price"),
        p.get("original_price"), p.get("discount_rate"), p.get("rating_average"),
        p.get("review_count"), p.get("seller_name"), p.get("extracted_at"))for p in products
    ]

    conn = get_connection()
    try:
        create_table(conn)
        # Thực hiện việc load vào
        with conn.cursor() as cur:
            cur.executemany(insert_sql, records)
        conn.commit()
        print(f"Load thành công {len(records)} sản phẩm vào DB")
    finally:
        conn.close()

if __name__ == "__main__":
    load_data()