with stg as (
    select * from {{ ref('stg_raw_retail_sales') }}
)

select distinct
    store_id,
    store_location
from stg
