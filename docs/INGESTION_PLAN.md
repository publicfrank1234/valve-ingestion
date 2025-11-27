# Valve Specification Ingestion Workflow

## Overview

This workflow extracts valve specifications from ValveMan.com product pages by:
1. Extracting URLs from sitemap
2. Scraping each product page
3. Using LLM to extract structured specifications
4. Storing in a searchable database

## Architecture

```
┌─────────────┐
│  Webhook    │  Trigger ingestion (sitemap URL or list of URLs)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Extract Sitemap    │  Parse sitemap.xml or process URL list
│  URLs               │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Loop Over URLs     │  Process each product page
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Scrape Page        │  Fetch HTML content
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Extract Specs      │  LLM extracts structured specs
│  (LLM Agent)        │  using valve-spec-schema.json
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Store in Database   │  Save to JSON file (or DB)
└─────────────────────┘
```

## Example: Spec Extraction from Product Page

**Input URL:** `https://valveman.com/products/1-2-SVF-Flow-Control-500F-Gate-Valve-Forged-Carbon-Steel-Body-Socket-Weld-Ends`

**Extracted Specs:**
```json
{
  "valveType": "Gate Valve",
  "size": {
    "nominalSize": "1/2\""
  },
  "materials": {
    "bodyMaterial": "Forged Carbon Steel",
    "specificGrade": "Carbon Steel"
  },
  "endConnections": {
    "inlet": "Socket Welded",
    "outlet": "Socket Welded"
  },
  "pressureRating": {
    "maxOperatingPressure": 1975,
    "pressureUnit": "psi",
    "pressureClass": "800"
  },
  "temperatureRating": {
    "maxTemperature": 850,
    "temperatureUnit": "°F"
  },
  "manufacturer": "SVF Flow Control",
  "modelNumber": "500F",
  "standards": ["API 602", "NACE MR0175"],
  "openingMethod": "Multi-Turn",
  "actuationMethod": "Manual",
  "sku": "500FCW03",
  "price": 55.99,
  "sourceUrl": "https://valveman.com/products/1-2-SVF-Flow-Control-500F-Gate-Valve-Forged-Carbon-Steel-Body-Socket-Weld-Ends",
  "extractedAt": "2025-01-27T10:00:00Z"
}
```

## Workflow Steps

### 1. Webhook Trigger
- Accepts: `sitemapUrl` or `urls[]` (array of product URLs)
- Optional: `baseUrl` (default: https://valveman.com)

### 2. Extract Sitemap URLs
- If `sitemapUrl` provided: fetch and parse sitemap.xml
- Extract all `/products/` URLs
- If `urls[]` provided: use directly

### 3. Loop Over URLs
- Process each URL sequentially (or in batches)
- Track progress: `processed/total`

### 4. Scrape Page
- Fetch HTML content
- Extract main content (remove nav, footer, etc.)
- Pass to LLM for extraction

### 5. LLM Spec Extraction
- Use valve-spec-schema.json as output schema
- Extract all available specifications
- Handle missing fields gracefully

### 6. Store Results
- Save to `valve-specs-db.json`
- Index by: SKU, URL, valveType, size, material
- Support incremental updates (skip if already exists)

## Database Schema

```json
{
  "specs": [
    {
      "id": "uuid",
      "sourceUrl": "https://valveman.com/products/...",
      "extractedAt": "ISO timestamp",
      "spec": { /* valve spec object */ }
    }
  ],
  "index": {
    "bySku": { "500FCW03": ["id1", "id2"] },
    "byUrl": { "https://...": "id1" },
    "byValveType": { "Gate Valve": ["id1", "id2"] }
  },
  "metadata": {
    "totalSpecs": 1234,
    "lastUpdated": "ISO timestamp",
    "sitemapUrl": "https://valveman.com/sitemap.xml"
  }
}
```

## Search API

After ingestion, enable search:
- Search by: valveType, size, material, pressure, temperature, endConnection
- Return matching specs with relevance score
- Support fuzzy matching for sizes (1/2" = 0.5")

## Implementation Files

1. `RFQ Valve Spec Ingestion.json` - n8n workflow
2. `valve-spec-extractor.js` - Code node for spec extraction
3. `valve-specs-db.json` - Database file (initial empty)
4. `app/api/ingest-valve-specs/route.ts` - Next.js API endpoint
5. `app/api/search-valve-specs/route.ts` - Search API endpoint

