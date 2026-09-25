
with source_data AS (
    SELECT *
    FROM {{source('ecommerce_source', 'raw_tiki_products')}}
)

SELECT
    product_id,
    TRIM(name) AS product_name,
    price,
    original_price,
    COALESCE(discount_rate, 0) AS discount_rate,
    COALESCE(rating_average, 0.0) AS rating_average,
    COALESCE(review_count, 0) AS review_count,
    COALESCE(seller_name, 'Unknown') AS seller_name,
    STR_TO_DATE(extracted_at, '%Y-%m-%d %H:%i:%s') AS extracted_at,
    loaded_at
FROM source_data
WHERE product_id IS NOT NULL