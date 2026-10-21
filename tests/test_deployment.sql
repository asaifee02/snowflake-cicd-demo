
EXECUTE IMMEDIATE $$
DECLARE
    TEST_FAILED EXCEPTION (
        -20001,
        'Snowflake deployment validation failed'
    );

    V_DUPLICATES NUMBER;
    V_INVALID NUMBER;
    V_MISSING_OBJECT NUMBER;

BEGIN
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

    IF (V_DUPLICATES > 0 OR V_INVALID > 0) THEN
        RAISE TEST_FAILED;
    END IF;

    RETURN 'PASS: Deployment data checks succeeded';
END;
$$;
