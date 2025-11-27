-- Valve Specifications Database Schema
-- PostgreSQL schema for storing extracted valve specifications

-- Main valve specifications table
CREATE TABLE IF NOT EXISTS valve_specs (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    spec_sheet_url TEXT,
    sku TEXT,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Price information
    starting_price DECIMAL(10, 2),
    msrp DECIMAL(10, 2),
    savings DECIMAL(10, 2),
    
    -- Basic specs (denormalized for easy querying)
    valve_type TEXT,
    size_nominal TEXT,
    body_material TEXT,
    max_pressure DECIMAL(10, 2),
    pressure_unit TEXT,
    pressure_class TEXT,
    max_temperature DECIMAL(10, 2),
    temperature_unit TEXT,
    end_connection_inlet TEXT,
    end_connection_outlet TEXT,
    
    -- Full normalized spec (JSONB for flexible querying)
    spec JSONB,
    
    -- Raw extracted specs (for reference/debugging)
    raw_specs JSONB,
    
    -- Full price info (JSONB)
    price_info JSONB
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_valve_type ON valve_specs(valve_type);
CREATE INDEX IF NOT EXISTS idx_size_nominal ON valve_specs(size_nominal);
CREATE INDEX IF NOT EXISTS idx_body_material ON valve_specs(body_material);
CREATE INDEX IF NOT EXISTS idx_pressure_class ON valve_specs(pressure_class);
CREATE INDEX IF NOT EXISTS idx_sku ON valve_specs(sku);
CREATE INDEX IF NOT EXISTS idx_source_url ON valve_specs(source_url);
CREATE INDEX IF NOT EXISTS idx_extracted_at ON valve_specs(extracted_at);

-- JSONB indexes for flexible querying
CREATE INDEX IF NOT EXISTS idx_spec_jsonb ON valve_specs USING GIN(spec);
CREATE INDEX IF NOT EXISTS idx_price_info_jsonb ON valve_specs USING GIN(price_info);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_valve_specs_updated_at 
    BEFORE UPDATE ON valve_specs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for easy querying
CREATE OR REPLACE VIEW valve_specs_summary AS
SELECT 
    id,
    source_url,
    spec_sheet_url,
    sku,
    valve_type,
    size_nominal,
    body_material,
    max_pressure,
    pressure_unit,
    pressure_class,
    max_temperature,
    temperature_unit,
    end_connection_inlet,
    starting_price,
    msrp,
    extracted_at
FROM valve_specs;

