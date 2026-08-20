with stg as (
    select * from {{ ref('stg_raw_retail_sales') }}
)

select distinct
    product_id,
    product_name,
    product_category
from stg
