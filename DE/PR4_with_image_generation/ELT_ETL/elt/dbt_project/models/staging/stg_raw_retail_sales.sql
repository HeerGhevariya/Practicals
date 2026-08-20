with source as (
    select * from {{ source('retail_raw', 'stg_raw_sales') }}
),

cleaned as (
    select
        transaction_id,
        coalesce(
            try_cast(transaction_date as timestamp),
            try_strptime(transaction_date, '%d-%m-%Y %H:%M:%S'),
            try_strptime(transaction_date, '%Y/%m/%d %H:%M:%S')
        ) as transaction_date,
        trim(customer_id) as customer_id,
        concat(upper(substring(trim(customer_name), 1, 1)), lower(substring(trim(customer_name), 2))) as customer_name,
        lower(trim(customer_email)) as customer_email,
        trim(store_id) as store_id,
        trim(store_location) as store_location,
        trim(product_id) as product_id,
        trim(product_name) as product_name,
        concat(upper(substring(trim(product_category), 1, 1)), lower(substring(trim(product_category), 2))) as product_category,
        try_cast(trim(quantity) as integer) as quantity,
        try_cast(replace(trim(unit_price), '$', '') as double) as unit_price,
        coalesce(try_cast(replace(trim(discount_amount), '$', '') as double), 0.0) as discount_amount,
        concat(upper(substring(trim(payment_method), 1, 1)), lower(substring(trim(payment_method), 2))) as payment_method
    from source
    where 
        coalesce(
            try_cast(transaction_date as timestamp),
            try_strptime(transaction_date, '%d-%m-%Y %H:%M:%S'),
            try_strptime(transaction_date, '%Y/%m/%d %H:%M:%S')
        ) is not null
        and try_cast(trim(quantity) as integer) > 0
        and try_cast(replace(trim(unit_price), '$', '') as double) > 0
)

select * from cleaned
