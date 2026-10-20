MERGE INTO SALES_DEV.RAW.SALES_TRANSACTIONS AS target
USING (
    SELECT
        COLUMN1 AS ORDER_ID,
        COLUMN2 AS REGION,
        COLUMN3 AS AMOUNT,
        COLUMN4 AS ORDER_DATE
    FROM VALUES
        (1, 'Mumbai', 1000.00, '2026-10-01'::DATE),
        (2, 'Pune',   2000.00, '2026-10-02'::DATE),
        (3, 'Mumbai', 1500.00, '2026-10-03'::DATE),
        (4, 'Delhi',  3000.00, '2026-10-04'::DATE),
        (5, 'Pune',    500.00, '2026-10-05'::DATE),
        (6, 'Delhi',  -100.00, '2026-10-06'::DATE)
) AS source
ON target.ORDER_ID = source.ORDER_ID
WHEN MATCHED THEN UPDATE SET
    REGION = source.REGION,
    AMOUNT = source.AMOUNT,
    ORDER_DATE = source.ORDER_DATE
WHEN NOT MATCHED THEN INSERT
    (ORDER_ID, REGION, AMOUNT, ORDER_DATE)
VALUES
    (source.ORDER_ID, source.REGION,
     source.AMOUNT, source.ORDER_DATE);