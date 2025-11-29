# Search and Indexing Architecture

## Current Search Implementation

### How Search Works

The search functionality is implemented in `search_specs.py` with the following approach:

1. **Dynamic Query Building**: Builds SQL WHERE clauses based on provided parameters
2. **Index-Optimized Queries**: Uses exact matches and prefix matches that can leverage indexes
3. **Compatibility Mapping**: Maps input values to compatible database values for better matching

### Search Function: `search_specs()`

**Parameters:**

- `valve_type`: Type of valve (e.g., "Gate Valve", "Ball Valve")
- `size_nominal`: Nominal size (e.g., "1/2", "3/4", "1")
- `body_material`: Body material (e.g., "Carbon Steel", "Stainless Steel")
- `pressure_class`: Pressure class (e.g., "800", "150", "300")
- `end_connection`: End connection type (e.g., "Socket-weld", "NPT", "Threaded")
- `max_results`: Maximum number of results (default: 10)

**Query Strategy:**

1. **Valve Type**: Uses `ILIKE` with prefix match (`valve_type ILIKE 'Gate Valve%'`)

   - Can use index for prefix searches
   - Case-insensitive matching

2. **Size**: Uses exact match (`size_nominal = '1/2'`)

   - Fastest lookup using index
   - No normalization needed (exact match required)

3. **Material**: Uses compatibility mapping + `IN` clause

   - Maps input to compatible materials (e.g., "CS" → ["Carbon Steel", "Forged Steel", "CS"])
   - Uses `IN` clause for exact matches (can use index)
   - Example: `body_material IN ('Carbon Steel', 'Forged Steel', 'CS')`

4. **Pressure Class**: Exact match with NULL handling

   - `(pressure_class = '800' OR pressure_class IS NULL)`
   - Allows matching when pressure class is not specified in database

5. **End Connection**: Matches either inlet or outlet
   - `(end_connection_inlet = 'Socket-weld' OR end_connection_outlet = 'Socket-weld')`
   - Handles cases where connection might be on either end

### Current Compatibility Mapping

**Material Compatibility** (in `search_specs.py`):

```python
MATERIAL_COMPATIBILITY = {
    'carbon steel': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS'],
    'cs': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS'],
    'forged steel': ['Forged Steel', 'Forged Carbon Steel', 'Carbon Steel'],
    'stainless steel': ['Stainless Steel', 'SS', '316SS', '304SS'],
    'ss': ['Stainless Steel', 'SS', '316SS', '304SS'],
}
```

## Indexing Strategy

### Single-Column Indexes (from `schema.sql`):

- `idx_valve_type` on `valve_type`
- `idx_size_nominal` on `size_nominal`
- `idx_body_material` on `body_material`
- `idx_pressure_class` on `pressure_class`
- `idx_sku` on `sku`
- `idx_source_url` on `source_url`
- `idx_extracted_at` on `extracted_at`

### Composite Indexes (from `add_performance_indexes.sql`):

- `idx_valve_size_material` on `(valve_type, size_nominal, body_material)`
  - Optimizes queries filtering by valve type + size + material
- `idx_size_material_pressure` on `(size_nominal, body_material, pressure_class)`
  - Optimizes queries filtering by size + material + pressure

### Partial Indexes:

- `idx_end_connection_inlet` on `end_connection_inlet` WHERE `end_connection_inlet IS NOT NULL`
- `idx_end_connection_outlet` on `end_connection_outlet` WHERE `end_connection_outlet IS NOT NULL`
- `idx_pressure_class_null` on `pressure_class` WHERE `pressure_class IS NOT NULL`

### JSONB Indexes:

- `idx_spec_jsonb` using GIN on `spec` (JSONB column)
- `idx_price_info_jsonb` using GIN on `price_info` (JSONB column)

## Query Performance

The search is optimized for:

1. **Exact matches** where possible (size, material via IN clause)
2. **Prefix matches** for text fields (valve_type)
3. **Index usage** through proper WHERE clause construction
4. **NULL handling** for optional fields (pressure_class, end_connection)

## Recommendations for Compatibility Mapping

To ensure comprehensive compatibility, we should:

1. **Analyze all distinct values** in the database for each column
2. **Group similar values** (e.g., "Socket-weld", "SW", "Socket Weld" → same group)
3. **Create bidirectional mappings** (input → database values, database values → searchable terms)
4. **Handle abbreviations** (CS, SS, NPT, SW, etc.)
5. **Handle case variations** (Carbon Steel, carbon steel, CARBON STEEL)
6. **Handle spelling variations** (Socket-weld, Socket weld, Socket-Weld)
