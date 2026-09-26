
WITH source_data AS (
    SELECT *
    FROM {{ source('ecommerce_source', 'raw_tiki_products') }}
),

ranked AS (
    SELECT
        product_id,
        TRIM(name) AS product_name,
        price,
        original_price,
        COALESCE(discount_rate, 0) AS discount_rate,
        COALESCE(rating_average, 0.0) AS rating_average,
        COALESCE(review_count, 0) AS review_count,
        COALESCE(seller_name, 'Unknown') AS seller_name,
        -- Cắt lấy 19 ký tự đầu và đổi 'T' thành khoảng trắng để parse an toàn
        STR_TO_DATE(LEFT(REPLACE(extracted_at, 'T', ' '), 19), '%Y-%m-%d %H:%i:%s') AS extracted_at,
        loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY product_id 
            ORDER BY STR_TO_DATE(LEFT(REPLACE(extracted_at, 'T', ' '), 19), '%Y-%m-%d %H:%i:%s') DESC
        ) AS rn
    FROM source_data
    WHERE product_id IS NOT NULL
)

SELECT
    product_id,
    product_name,
    price,
    original_price,
    discount_rate,
    rating_average,
    review_count,
    seller_name,
    extracted_at,
    loaded_at
FROM ranked
WHERE rn = 1