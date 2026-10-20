
INSERT INTO SALES_DEV.RAW.SALES_EVENTS
(
    EVENT_ID, BATCH_ID, ORDER_ID, REGION,
    AMOUNT, ORDER_DATE, SOURCE_UPDATED_AT
)
SELECT
    column1, column2, column3, column4,
    column5, column6, TO_TIMESTAMP_NTZ(column7)
FROM VALUES
    (101, 1, '1', 'Mumbai', '1000', '2026-10-01', '2026-10-01 09:00:00'),
    (102, 1, '2', 'Pune',   '2000', '2026-10-02', '2026-10-02 09:00:00'),
    (103, 1, '3', 'Mumbai', '1500', '2026-10-03', '2026-10-03 09:00:00'),
    (104, 1, '4', 'Delhi',  '3000', '2026-10-04', '2026-10-04 09:00:00'),
    (105, 1, '5', 'Pune',    '500', '2026-10-05', '2026-10-05 09:00:00'),
    (106, 1, '6', 'Delhi',  '-100', '2026-10-06', '2026-10-06 09:00:00');
