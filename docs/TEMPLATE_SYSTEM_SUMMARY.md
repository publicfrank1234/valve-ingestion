# Template-Based Extraction System - Summary

## What We Built

A complete template-based extraction system that replaces the unified spec approach with component-type-specific templates. This system allows each component type (valve, resistor, capacitor, etc.) to have its own specialized extraction rules and spec fields.

## Key Features

### ✅ Component-Type-Specific Templates

- Each component type has its own template
- Different spec fields for different component types
- Specialized extraction rules per component type

### ✅ Automatic Template Matching

- Analyzes page title, URL, and HTML structure
- Scores templates against page indicators
- Automatically selects best matching template

### ✅ AI-Powered Template Generation

- When no template matches, AI agent analyzes the page
- Generates new template with extraction rules
- Stores template for future use
- Systematically builds template library

### ✅ Template Management

- Track template usage and success rates
- Monitor extraction performance
- Version templates
- Easy template updates

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Template-Based Extraction System            │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Template   │    │   Template   │    │   Template   │
│   Manager    │    │  Extractor   │    │   Generator   │
│              │    │              │    │    (AI)        │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │   PostgreSQL     │
                  │   Database       │
                  └──────────────────┘
```

## How It Addresses Your Requirements

### 1. Component-Specific Specs ✅

**Your Requirement**: "Each component type should have their own spec"

**Solution**: Each template defines its own `specFields` array. For example:

- Gate Valve: `valveType`, `size`, `pressureRating`, `bodyMaterial`, `endConnection`
- Resistor: `resistance`, `tolerance`, `powerRating`, `packageType`

### 2. Template-Based Extraction ✅

**Your Requirement**: "Each page should have a template related with the component"

**Solution**: Templates include `pagePatterns` that identify component types:

- Title keywords
- URL patterns
- HTML markers

### 3. Template Matching ✅

**Your Requirement**: "For each new product page, find if it's a new template or existing template"

**Solution**: `TemplateManager.find_matching_template()`:

- Extracts page indicators
- Scores against all templates
- Returns best match if score > 0.7

### 4. AI Agent for New Templates ✅

**Your Requirement**: "If you don't find all the spec, you can ask the AI agent to look at the webpage and tell us what are the key specs"

**Solution**: `AITemplateGenerator`:

- Analyzes HTML structure
- Identifies component type
- Determines spec fields
- Generates extraction rules
- Creates complete template JSON

### 5. Systematic Template Building ✅

**Your Requirement**: "Systematically building new templates"

**Solution**:

- Templates stored in database
- Usage tracked automatically
- Success rates monitored
- Easy to review and improve

## File Structure

```
valve-spec-ingestion/
├── database/
│   └── template_schema.sql          # Database schema for templates
├── extraction/
│   ├── template_manager.py           # Template storage and retrieval
│   ├── template_extractor.py         # Extraction using templates
│   ├── ai_template_generator.py      # AI agent for template generation
│   ├── template_based_extractor.py  # Main orchestrator
│   ├── example_templates.py          # Example templates
│   └── setup_templates.py            # Setup script
└── docs/
    ├── TEMPLATE_BASED_EXTRACTION_ARCHITECTURE.md
    ├── TEMPLATE_SYSTEM_USAGE.md
    └── TEMPLATE_SYSTEM_SUMMARY.md    # This file
```

## Example Workflow

### Scenario: New Gate Valve Page

1. **Fetch Page**: `https://valveman.com/products/gate-valve-1-2-inch`

2. **Extract Indicators**:

   - Title: "1/2\" Gate Valve - Carbon Steel"
   - URL: `/products/gate-valve-1-2-inch`
   - HTML: Contains "Technical Specifications" section

3. **Match Templates**:

   - `gate_valve_v1`: Score 0.95 ✅ (matches!)

4. **Extract Using Template**:

   - Uses `gate_valve_v1` extraction rules
   - Extracts: `valveType`, `size`, `pressureRating`, `bodyMaterial`, `endConnection`
   - Validates required fields

5. **Log Usage**:
   - Records successful extraction
   - Updates template statistics

### Scenario: New Resistor Page (No Template)

1. **Fetch Page**: `https://example.com/products/resistor-0805-10k`

2. **Extract Indicators**:

   - Title: "0805 10K Resistor"
   - URL: `/products/resistor-0805-10k`
   - HTML: Contains resistor specifications

3. **Match Templates**:

   - No match found (score < 0.7)

4. **AI Agent Called**:

   - Analyzes HTML structure
   - Identifies: Component type = "Resistor"
   - Finds spec fields: `resistance`, `tolerance`, `powerRating`, `packageType`
   - Generates extraction rules

5. **Store New Template**:

   - Template ID: `resistor_0805_v1`
   - Saved to database

6. **Extract Using New Template**:
   - Uses newly generated template
   - Extracts all specs successfully

## Benefits

1. **Flexibility**: Each component type has optimized extraction
2. **Scalability**: Easy to add new component types
3. **Accuracy**: Specialized rules improve extraction quality
4. **Maintainability**: Update templates independently
5. **Automation**: AI generates templates for new types
6. **Tracking**: Monitor template performance

## Next Steps

1. **Test the System**:

   ```bash
   python extraction/setup_templates.py
   python extraction/template_based_extractor.py <url>
   ```

2. **Add More Templates**:

   - Create templates for other valve types
   - Add templates for other component categories
   - Use AI to generate templates automatically

3. **Integrate with Existing System**:

   - Replace unified spec extraction with template-based
   - Update n8n workflows to use templates
   - Migrate existing extraction logic

4. **Monitor and Improve**:
   - Review template success rates
   - Refine extraction rules
   - Update templates based on results

## Questions?

See the detailed documentation:

- **Architecture**: `TEMPLATE_BASED_EXTRACTION_ARCHITECTURE.md`
- **Usage**: `TEMPLATE_SYSTEM_USAGE.md`

