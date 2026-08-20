with stg as (
    select * from {{ ref('stg_raw_retail_sales') }}
)

select distinct
    customer_id,
    customer_name,
    customer_email
from stg
