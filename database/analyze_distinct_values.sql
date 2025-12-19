-- SQL script to analyze distinct values in valve_specs table
-- Run this directly in your PostgreSQL/Supabase database to see all distinct values

-- 1. VALVE TYPE - Distinct values with counts
SELECT 
    'valve_type' as column_name,
    valve_type as value,
    COUNT(*) as count
FROM valve_specs
WHERE valve_type IS NOT NULL
GROUP BY valve_type
ORDER BY count DESC, valve_type;

-- 2. SIZE NOMINAL - Distinct values with counts
SELECT 
    'size_nominal' as column_name,
    size_nominal as value,
    COUNT(*) as count
FROM valve_specs
WHERE size_nominal IS NOT NULL
GROUP BY size_nominal
ORDER BY 
    CASE 
        WHEN size_nominal ~ '^[0-9]+(\.[0-9]+)?$' THEN CAST(size_nominal AS NUMERIC)
        WHEN size_nominal ~ '^[0-9]+/[0-9]+$' THEN 
            CAST(SPLIT_PART(size_nominal, '/', 1) AS NUMERIC) / CAST(SPLIT_PART(size_nominal, '/', 2) AS NUMERIC)
        ELSE 999
    END,
    size_nominal;

-- 3. BODY MATERIAL - Distinct values with counts
SELECT 
    'body_material' as column_name,
    body_material as value,
    COUNT(*) as count
FROM valve_specs
WHERE body_material IS NOT NULL
GROUP BY body_material
ORDER BY count DESC, body_material;

-- 4. PRESSURE CLASS - Distinct values with counts
SELECT 
    'pressure_class' as column_name,
    pressure_class as value,
    COUNT(*) as count
FROM valve_specs
WHERE pressure_class IS NOT NULL
GROUP BY pressure_class
ORDER BY 
    CASE 
        WHEN pressure_class ~ '^[0-9]+$' THEN CAST(pressure_class AS INTEGER)
        ELSE 999
    END,
    pressure_class;

-- 5. END CONNECTION INLET - Distinct values with counts
SELECT 
    'end_connection_inlet' as column_name,
    end_connection_inlet as value,
    COUNT(*) as count
FROM valve_specs
WHERE end_connection_inlet IS NOT NULL
GROUP BY end_connection_inlet
ORDER BY count DESC, end_connection_inlet;

-- 6. END CONNECTION OUTLET - Distinct values with counts
SELECT 
    'end_connection_outlet' as column_name,
    end_connection_outlet as value,
    COUNT(*) as count
FROM valve_specs
WHERE end_connection_outlet IS NOT NULL
GROUP BY end_connection_outlet
ORDER BY count DESC, end_connection_outlet;

-- 7. COMBINED END CONNECTIONS (all unique values from both inlet and outlet)
SELECT 
    'end_connection_all' as column_name,
    value,
    COUNT(*) as count
FROM (
    SELECT end_connection_inlet as value FROM valve_specs WHERE end_connection_inlet IS NOT NULL
    UNION ALL
    SELECT end_connection_outlet as value FROM valve_specs WHERE end_connection_outlet IS NOT NULL
) combined
GROUP BY value
ORDER BY count DESC, value;

-- Summary: Total distinct values per column
SELECT 
    'Summary' as report_type,
    'valve_type' as column_name,
    COUNT(DISTINCT valve_type) as distinct_count,
    COUNT(*) as total_records,
    COUNT(*) - COUNT(valve_type) as null_count
FROM valve_specs
UNION ALL
SELECT 
    'Summary',
    'size_nominal',
    COUNT(DISTINCT size_nominal),
    COUNT(*),
    COUNT(*) - COUNT(size_nominal)
FROM valve_specs
UNION ALL
SELECT 
    'Summary',
    'body_material',
    COUNT(DISTINCT body_material),
    COUNT(*),
    COUNT(*) - COUNT(body_material)
FROM valve_specs
UNION ALL
SELECT 
    'Summary',
    'pressure_class',
    COUNT(DISTINCT pressure_class),
    COUNT(*),
    COUNT(*) - COUNT(pressure_class)
FROM valve_specs
UNION ALL
SELECT 
    'Summary',
    'end_connection_inlet',
    COUNT(DISTINCT end_connection_inlet),
    COUNT(*),
    COUNT(*) - COUNT(end_connection_inlet)
FROM valve_specs
UNION ALL
SELECT 
    'Summary',
    'end_connection_outlet',
    COUNT(DISTINCT end_connection_outlet),
    COUNT(*),
    COUNT(*) - COUNT(end_connection_outlet)
FROM valve_specs;









