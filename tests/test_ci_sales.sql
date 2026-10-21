
EXECUTE IMMEDIATE $$
DECLARE
    TEST_FAILED EXCEPTION (
        -20001,
        'Sales integration test failed'
    );

    V_COUNT NUMBER;
    V_TOTAL NUMBER(12,2);
    V_DUPLICATES NUMBER;
    V_INVALID NUMBER;
    V_ORDER_2 NUMBER(12,2);

BEGIN
    SELECT COUNT(*)
      INTO :V_COUNT
    FROM <% database %>.STAGING.SALES_CLEAN;

    SELECT COALESCE(SUM(TOTAL_SALES), 0)
      INTO :V_TOTAL
    FROM <% database %>.ANALYTICS.SALES_SUMMARY;

    SELECT COUNT(*)
      INTO :V_DUPLICATES
    FROM (
        SELECT ORDER_ID
        FROM <% database %>.STAGING.SALES_CLEAN
        GROUP BY ORDER_ID
        HAVING COUNT(*) > 1
    );

    SELECT COUNT(*)
      INTO :V_INVALID
    FROM <% database %>.STAGING.SALES_CLEAN
    WHERE ORDER_ID IS NULL
       OR REGION IS NULL
       OR TRIM(REGION) = ''
       OR AMOUNT IS NULL
       OR AMOUNT <= 0
       OR ORDER_DATE IS NULL
       OR SOURCE_UPDATED_AT IS NULL;

    SELECT MAX(AMOUNT)
      INTO :V_ORDER_2
    FROM <% database %>.STAGING.SALES_CLEAN
    WHERE ORDER_ID = 2;

    IF (
        V_COUNT <> 6
        OR V_TOTAL <> 8900
        OR V_DUPLICATES <> 0
        OR V_INVALID <> 0
        OR V_ORDER_2 IS DISTINCT FROM 2200
    ) THEN
        RAISE TEST_FAILED;
    END IF;

    RETURN 'PASS: Snowflake integration tests passed';
END;
$$;
