with stg as (
    select * from {{ ref('stg_raw_retail_sales') }}
)

select
    transaction_id,
    transaction_date,
    customer_id,
    product_id,
    store_id,
    quantity,
    unit_price,
    discount_amount,
    round((quantity * unit_price) - discount_amount, 2) as net_amount,
    payment_method
from stg
