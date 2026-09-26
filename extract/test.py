from dataclasses import field
import requests
import time
import json
from datetime import datetime, timezone
import os
# ELT

# Step 1 : gọi thử api tiki & kiểm tra kết nối

# URL lấy danh sách sản phẩm điện thoại - máy tính bảng
url = "https://tiki.vn/api/personalish/v1/blocks/listings"
# Endpoint trên là api nội bộ Tiki dùng để render trang danh mục sphẩm

# params là query, thư viện requests sẽ tự động ghép vào url để lấy sp
params = {
    "category": 1789,
    "page": 1,
    "limit": 10
}

# User-agent để tránh request mặc định(bị nhận diện là bot) -> Lỗi 403 Forbidden
# Headers này giả lập request xuất phát từ chrome thật trên mac
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
# respone.json() trả về chuỗi JSON. Hàm .join() parse nó thành Python dic
response = requests.get(url, params=params, headers=headers)

# Dùng .get("data", []) thay vì data["data"] để phòng th API trả về lỗi
# hoặc thay đổi cấu trúc, code sẽ k bị crash KeyError
print(f"Status Code: {response.status_code}")
data = response.json()
products = data.get("data", [])
print(f"Lấy thành công {len(products)} sản phẩm")
if products:
    print(f"Sản phẩm đầu tiên: {products[0].get('name')} - Gía: {products[0].get('price')}VNĐ")

# Step 2: Chuẩn hoá dữ liệu thô (Schema Parsing)

# Concept: Mỗi sản phẩm -> trả về API có tới 50+ trường tt khác nhau
# Nhiều trường bị None hoặc k cần thiết
# -> Nhiệm vụ: bóc tách đúng những trường hợp cốt lỗi (ID, giá bán, giá gốc, ...) và ép kiểu dữ liệu an toàn

# Cập nhật lại tiki.py để chuẩn hoá cấu trúc và dữ liệu

# Hàm parse_product -> sản phẩm dưới dạng dic
def parse_product(item: dict) -> dict:
    return {
        "product_id": item.get("id"),
        "name": item.get("name"),
        "price": item.get("price"),
        "original_price": item.get("original_price"),
        "discount_rate": item.get("discount_rate"),
        "rating_average": item.get("rating_average"),
        "review_count": item.get("review_count"),
        "seller_name": item.get("seller_name"),
    # Giúp xây dựng dữ liệu chuỗi thời gian (time-series) để theo dỡi lịch sử giá
    "extracted_at": datetime.now(timezone.utc).isoformat()
    }
# fetch_product -> fetch từ url để lấy sản phẩm
def fetch_products(category_id: int = 1789, page = 1, limit: int = 10) -> list[dict]:
    url = "https://tiki.vn/api/personalish/v1/blocks/listings"
    params = {
        "category": category_id,
        "page": page,
        "limit": limit
    }
    # Tránh bị lỗi 403 Forbidden
    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
    }

    # Lấy từ hàm requests -> như người thật tránh bị quét từ BOT
    respone = requests.get(url, params = params, headers = headers)
    respone.raise_for_status() # Báo lỗi nếu HTTP status != 200

    raw_product = respone.json().get("data", [])
    return [parse_product(p) for p in raw_product]

# Step 3: Phân trang (Pagination) & chống bị chặn IP (Rate Limiting)

# Concept: thực tế, 1 danh mục có hàng ngàn sản phẩm chia làm nhiều trang
# Nếu gửi request liên tục với tốc độc ao, hệ thống chống Bot Spam sẽ chặn IP của bạn ngay lập tức
# -> Duyệt qua vòng lặp và chèn 1 khoảng nghỉ vào giữa các lần gọi API

def extract_category(category_id: int = 1789, max_pages: int = 3) -> list[dict]:
    all_product = []

    for page in range(1, max_pages + 1):
        print(f"Đang cào trang {page}/ {max_pages}...")
        try:
            products = fetch_products(category_id=category_id, page=page, limit=10)
            if not products:
                print("Đã hết sản phẩm")
                break
            all_product.extend(products)
            print(f"Trang {page}: lấy được {len(products)} sản phẩm")
            # Nghỉ 1.5s tránh bị ban IP từ Tiki
            time.sleep(1.5)
        except Exception as e:
            print(f"Lỗi khi cào trang {page}: {e}")
            break

    return all_product

# Step 4: Metadata (Thời gian cào) & Landing Zone (Lưu file JSON)

# Concept: giá spam sẽ biến thiên liên tục theo thời gian nên bắt buộc phải gắn mốc thời điểm
# cào dữ liệu theo thời gian quốc tế UTC để phục vụ việc phân tích giá sau này
# Trong quy trình ELT, việc lưu dữ liệu cào thành file trung gian (Landing Zone)
# giúp bảo toàn dữ liệu nếu tầng DB phía sau gặp sự cố, tránh việc phải cào lại từ đầu

# Thêm "extracted_at" vào hàm parse_products
    # ?extracted_at": datetime.now(timezone.utc).isoformat()

# Hàm lưu dữ liệu vào Landing Zone(JSON thô)
def save_to_json(data: list[dict], filepath: str = "data/raw_product.json"):

    # Tự động tạo thư mục cha nếu chưa có
    os.makedirs(os.path.dirname(filepath), exist_ok = True)

    # Mở File ghi với mã hoá utf-8
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii = False, indent = 2)
    print(f"Đã Lưu {len(data)} sản phẩm vào: {filepath}")

if __name__ == "__main__":
    # Step 2:
    products = fetch_products(category_id=1789, page=1, limit=5)
    print(f"Bóc tách thành công {len(products)} sản phẩm: ")
    for p in products:
        print(p)
    # Step 3:
    data = extract_category(category_id = 1789, max_pages = 3)
    print(f"\nĐã cào được: {len(data)} sản phẩm từ Tiki")
    # Step 4:
    save_to_json(data)
