import os
import json
import pymysql
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# 1. Cấu hình giao diện Streamlit (Full width)
st.set_page_config(
    page_title="Tiki E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Hide all Streamlit UI elements */
    #MainMenu, header, footer, .stAppDeployButton { display: none !important; }
    
    /* Remove all padding from main container */
    .stApp { padding: 0 !important; margin: 0 !important; }
    .block-container { 
        padding: 0 !important; 
        margin: 0 !important; 
        max-width: 100% !important;
    }
    
    /* Remove iframe border and make it fill viewport */
    iframe {
        border: none !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Đọc biến môi trường từ .env
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CURRENT_DIR, '..', '.env'))

DB_HOST = os.getenv('mysql_host')
DB_PORT = int(os.getenv('mysql_port', 3306))
DB_USER = os.getenv('mysql_user')
DB_PASS = os.getenv('mysql_password')
DB_NAME = os.getenv('mysql_database')

# 3. Hàm liên kết (bundle) index.html, style.css và script.js
def get_bundled_dashboard_html():
    try:
        with open(os.path.join(CURRENT_DIR, "style.css"), "r", encoding="utf-8") as f:
            css = f.read()
        with open(os.path.join(CURRENT_DIR, "script.js"), "r", encoding="utf-8") as f:
            js = f.read()
        with open(os.path.join(CURRENT_DIR, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()

        # Nhúng trực tiếp style.css và script.js vào khung HTML
        bundled_html = html.replace(
            '<link rel="stylesheet" href="style.css">',
            f'<style>\n{css}\n</style>'
        ).replace(
            '<script src="script.js"></script>',
            f'<script>\n{js}\n</script>'
        )
        return bundled_html
    except Exception as e:
        return f"<h3>Lỗi khi đọc file HTML/CSS/JS: {e}</h3>"

# 4. Hàm kết nối và truy vấn dữ liệu từ MySQL (có cache)
@st.cache_data(ttl=300)
def load_data():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cur:
            # Đọc dữ liệu Staging
            cur.execute("""
                SELECT 
                    product_id, product_name, price, original_price, 
                    discount_rate, rating_average, review_count, 
                    seller_name, extracted_at
                FROM stg_tiki_products
            """)
            df_products = pd.DataFrame(cur.fetchall())

            # Đọc dữ liệu Marts
            cur.execute("""
                SELECT 
                    seller_name, total_products, avg_price, 
                    min_price, max_price, avg_rating, total_reviews
                FROM fct_seller_summary
                ORDER BY total_products DESC
            """)
            df_sellers = pd.DataFrame(cur.fetchall())

        # Ép kiểu dữ liệu số an toàn
        num_cols_prod = ['price', 'original_price', 'discount_rate', 'rating_average', 'review_count']
        for col in num_cols_prod:
            if col in df_products.columns:
                df_products[col] = pd.to_numeric(df_products[col], errors='coerce').fillna(0)

        num_cols_sellers = ['total_products', 'avg_price', 'min_price', 'max_price', 'avg_rating', 'total_reviews']
        for col in num_cols_sellers:
            if col in df_sellers.columns:
                df_sellers[col] = pd.to_numeric(df_sellers[col], errors='coerce').fillna(0)

        return df_products, df_sellers
    finally:
        conn.close()

# 5. Tải dữ liệu MySQL và nhúng trực tiếp vào Dashboard HTML
try:
    df_products, df_sellers = load_data()
except Exception as e:
    df_products, df_sellers = pd.DataFrame(), pd.DataFrame()

sellers_json = df_sellers.to_json(orient='records', force_ascii=False) if not df_sellers.empty else '[]'
products_json = df_products.to_json(orient='records', force_ascii=False) if not df_products.empty else '[]'

dashboard_html = get_bundled_dashboard_html()
dashboard_html = dashboard_html.replace(
    '/* INJECT_SELLERS */',
    f'const SELLERS = {sellers_json};'
).replace(
    '/* INJECT_PRODUCTS */',
    f'const PRODUCTS = {products_json};'
)

# Render full viewport
components.html(dashboard_html, height=2000, scrolling=True)
