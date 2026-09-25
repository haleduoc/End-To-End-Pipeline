
WITH staging AS (
    SELECT * FROM {{ref('stg_tiki_products')}}
)

SELECT
    seller_name,
    COUNT(product_id) AS total_products,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(MIN(price), 2) AS min_price,
    ROUND(MAX(price), 2) AS max_price,
    ROUND(AVG(rating_average), 2) AS avg_rating,
    SUM(review_count) AS total_reviews 
FROM staging
GROUP BY seller_name
ORDER BY total_products DESC