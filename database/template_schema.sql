-- Extraction Templates Database Schema
-- PostgreSQL schema for storing component-type-specific extraction templates

-- Main extraction templates table
CREATE TABLE IF NOT EXISTS extraction_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    component_type TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'valve', 'resistor', 'capacitor', 'actuator', etc.
    version TEXT NOT NULL DEFAULT '1.0',
    template_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT DEFAULT 'ai_agent',  -- 'ai_agent', 'manual', 'user_id'
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 4),  -- 0.0000 to 1.0000
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    notes TEXT
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_templates_component_type ON extraction_templates(component_type);
CREATE INDEX IF NOT EXISTS idx_templates_category ON extraction_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_active ON extraction_templates(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_templates_template_id ON extraction_templates(template_id);
CREATE INDEX IF NOT EXISTS idx_templates_jsonb ON extraction_templates USING GIN(template_data);
CREATE INDEX IF NOT EXISTS idx_templates_last_used ON extraction_templates(last_used_at DESC);

-- Template usage tracking table
CREATE TABLE IF NOT EXISTS template_usage_log (
    id SERIAL PRIMARY KEY,
    template_id TEXT NOT NULL REFERENCES extraction_templates(template_id),
    source_url TEXT NOT NULL,
    extraction_success BOOLEAN NOT NULL,
    extracted_fields_count INTEGER,
    missing_required_fields TEXT[],  -- Array of missing required field names
    extraction_time_ms INTEGER,  -- Time taken for extraction in milliseconds
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_usage_log_template_id ON template_usage_log(template_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_used_at ON template_usage_log(used_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_log_success ON template_usage_log(extraction_success);

-- Function to update template usage statistics
CREATE OR REPLACE FUNCTION update_template_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE extraction_templates
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW(),
        success_rate = (
            SELECT 
                CASE 
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE SUM(CASE WHEN extraction_success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL
                END
            FROM template_usage_log
            WHERE template_id = NEW.template_id
        )
    WHERE template_id = NEW.template_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update template stats
CREATE TRIGGER update_template_stats_trigger
    AFTER INSERT ON template_usage_log
    FOR EACH ROW
    EXECUTE FUNCTION update_template_stats();

-- View for template summary
CREATE OR REPLACE VIEW template_summary AS
SELECT 
    et.template_id,
    et.component_type,
    et.category,
    et.version,
    et.created_at,
    et.created_by,
    et.usage_count,
    et.success_rate,
    et.last_used_at,
    et.is_active,
    COUNT(tul.id) FILTER (WHERE tul.extraction_success = true) as successful_extractions,
    COUNT(tul.id) FILTER (WHERE tul.extraction_success = false) as failed_extractions,
    AVG(tul.extraction_time_ms) FILTER (WHERE tul.extraction_time_ms IS NOT NULL) as avg_extraction_time_ms
FROM extraction_templates et
LEFT JOIN template_usage_log tul ON et.template_id = tul.template_id
GROUP BY et.id, et.template_id, et.component_type, et.category, et.version, 
         et.created_at, et.created_by, et.usage_count, et.success_rate, 
         et.last_used_at, et.is_active;

-- Function to get best matching template for a component type
CREATE OR REPLACE FUNCTION get_best_template(
    p_component_type TEXT,
    p_category TEXT DEFAULT NULL
)
RETURNS TABLE (
    template_id TEXT,
    component_type TEXT,
    category TEXT,
    version TEXT,
    template_data JSONB,
    success_rate DECIMAL,
    usage_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        et.template_id,
        et.component_type,
        et.category,
        et.version,
        et.template_data,
        et.success_rate,
        et.usage_count
    FROM extraction_templates et
    WHERE et.is_active = true
        AND (
            et.component_type ILIKE '%' || p_component_type || '%'
            OR p_component_type ILIKE '%' || et.component_type || '%'
        )
        AND (p_category IS NULL OR et.category = p_category)
    ORDER BY 
        et.success_rate DESC NULLS LAST,
        et.usage_count DESC,
        et.last_used_at DESC NULLS LAST
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

