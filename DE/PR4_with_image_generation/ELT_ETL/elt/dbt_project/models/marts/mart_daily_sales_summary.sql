with fact as (
    select * from {{ ref('fact_sales') }}
)

select
    cast(transaction_date as date) as sales_date,
    store_id,
    count(transaction_id) as total_transactions,
    sum(quantity) as total_units_sold,
    round(sum(quantity * unit_price), 2) as gross_revenue,
    round(sum(discount_amount), 2) as total_discounts,
    round(sum(net_amount), 2) as net_revenue
from fact
group by cast(transaction_date as date), store_id
