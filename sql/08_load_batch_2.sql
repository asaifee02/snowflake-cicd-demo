
INSERT INTO SALES_DEV.RAW.SALES_EVENTS
(
    EVENT_ID, BATCH_ID, ORDER_ID, REGION,
    AMOUNT, ORDER_DATE, SOURCE_UPDATED_AT
)
SELECT
    column1, column2, column3, column4,
    column5, column6, TO_TIMESTAMP_NTZ(column7)
FROM VALUES
    (201, 2, '2', 'Pune', '2200', '2026-10-02', '2026-10-10 10:00:00'),
    (202, 2, '7', 'Delhi', '700', '2026-10-07', '2026-10-10 11:00:00'),
    (203, 2, '2', 'Pune', '1900', '2026-10-02', '2026-10-01 10:00:00'),
    (204, 2, '8', '   ', '400', '2026-10-08', '2026-10-10 12:00:00');
