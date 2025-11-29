-- Performance optimization indexes for valve_specs table
-- These composite indexes speed up common query patterns

-- Common search pattern: valve_type + size + material
CREATE INDEX IF NOT EXISTS idx_valve_size_material 
ON valve_specs(valve_type, size_nominal, body_material);

-- Common search pattern: size + material + pressure_class
CREATE INDEX IF NOT EXISTS idx_size_material_pressure 
ON valve_specs(size_nominal, body_material, pressure_class);

-- For end connection searches
CREATE INDEX IF NOT EXISTS idx_end_connection_inlet 
ON valve_specs(end_connection_inlet) 
WHERE end_connection_inlet IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_end_connection_outlet 
ON valve_specs(end_connection_outlet) 
WHERE end_connection_outlet IS NOT NULL;

-- For NULL-safe pressure_class searches
CREATE INDEX IF NOT EXISTS idx_pressure_class_null 
ON valve_specs(pressure_class) 
WHERE pressure_class IS NOT NULL;

