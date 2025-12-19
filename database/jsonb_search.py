#!/usr/bin/env python3
"""
JSONB-based tiered search for component-system tables.

Self-contained implementation - no external dependencies.
Searches tables with tech_specs and metadata JSONB columns.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus


def get_db_connection():
    """Get database connection using same logic as search_specs.py."""
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Otherwise use individual environment variables
    password = os.getenv('DB_PASSWORD', 'valve@123')
    
    # URL encode password if needed
    encoded_password = quote_plus(password)
    
    # Try connection pooler first (if pooler host is set) - supports IPv4
    pooler_host = os.getenv('DB_POOLER_HOST')
    if pooler_host:
        pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
        pooler_port = os.getenv('DB_POOLER_PORT', '5432')  # Default to 5432 (transaction mode) or 6543 (session mode)
        conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
        print(f"🔌 Attempting pooler connection: {pooler_host}:{pooler_port}")
        try:
            conn = psycopg2.connect(conn_string)
            print(f"✅ Pooler connection successful")
            return conn
        except Exception as e:
            print(f"⚠️  Pooler connection failed: {e}")
            print("Trying direct connection...")
    
    # Fall back to direct connection (or use DB_HOST if it's already a pooler)
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db.deaohsesihodomvhqlxe.supabase.co'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=password,
        sslmode='require'
    )


def normalize_size(size: Optional[str]) -> Optional[str]:
    """Normalize size format for matching."""
    if not size:
        return None
    
    size_clean = size.strip().replace('"', '').replace("'", '')
    
    size_map = {
        '1 1/2': '1-1/2',
        '1 1/4': '1-1/4',
        '2 1/2': '2-1/2',
        '3 1/2': '3-1/2',
    }
    
    return size_map.get(size_clean, size_clean)


def extract_pressure_number(pressure_str: Optional[str]) -> Optional[int]:
    """Extract numeric pressure value from string."""
    if not pressure_str:
        return None
    
    match = re.search(r'(\d+)', str(pressure_str))
    if match:
        return int(match.group(1))
    return None


def get_component_tables(conn) -> List[str]:
    """Get list of all component spec tables (excluding old valve_specs)."""
    cursor = conn.cursor()
    # Look for tables ending in _specs (but not valve_specs)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%_specs'
        AND table_name != 'valve_specs'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    # Debug: print what we found
    print(f"📊 get_component_tables found {len(tables)} tables")
    if tables:
        print(f"   First 5: {tables[:5]}")
    else:
        # Check what tables actually exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%spec%' OR table_name LIKE '%valve%')
            ORDER BY table_name
        """)
        all_related = [row[0] for row in cursor.fetchall()]
        cursor.close()
        print(f"   Related tables found: {all_related[:10]}")
    
    return tables


def build_union_query(tables: List[str]) -> str:
    """Build UNION query for all component tables."""
    if not tables:
        return None
    
    union_parts = []
    for table in tables:
        union_parts.append(f"""
            SELECT 
                id,
                source_url,
                component_type,
                metadata,
                tech_specs,
                tech_specs->>'size' as size,
                tech_specs->>'item' as item,
                tech_specs->>'pressure_rating' as pressure_rating,
                tech_specs->>'pressure_class' as pressure_class,
                tech_specs->>'body_material' as body_material,
                tech_specs->>'seat_material' as seat_material,
                tech_specs->>'connection_type' as connection_type,
                tech_specs->>'end_connection' as end_connection,
                tech_specs->>'body_style' as body_style
            FROM {table}
            WHERE tech_specs IS NOT NULL
        """)
    
    return " UNION ALL ".join(union_parts)


def calculate_score(result: Dict, normalized_specs: Dict) -> Tuple[float, int]:
    """Calculate match score (0-1) and determine tier."""
    score = 0.0
    matched_fields = []
    
    # Size match (40% weight)
    requested_size = normalize_size(normalized_specs.get('size'))
    product_size = normalize_size(result.get('size'))
    if requested_size and product_size:
        if requested_size == product_size:
            score += 0.4
            matched_fields.append('size')
    elif not requested_size:
        score += 0.4
    
    # Valve type match (30% weight)
    requested_type = normalized_specs.get('valveType', '').lower()
    product_type = (result.get('item') or result.get('component_type') or '').lower()
    if requested_type:
        if requested_type in product_type or product_type in requested_type:
            score += 0.3
            matched_fields.append('valveType')
    else:
        score += 0.3
    
    # Pressure match (15% weight)
    requested_pressure = extract_pressure_number(normalized_specs.get('pressureRating'))
    product_pressure = extract_pressure_number(result.get('pressure_rating') or result.get('pressure_class'))
    if requested_pressure and product_pressure:
        if product_pressure >= requested_pressure:
            score += 0.15
            matched_fields.append('pressureRating')
    elif not requested_pressure:
        score += 0.15
    
    # Material match (10% weight)
    requested_material = (normalized_specs.get('material') or '').lower()
    product_material = (result.get('body_material') or '').lower()
    if requested_material:
        if requested_material in product_material or product_material in requested_material:
            score += 0.1
            matched_fields.append('material')
    else:
        score += 0.1
    
    # Connection match (5% weight)
    requested_connection = (normalized_specs.get('endConnection') or '').lower()
    product_connection = (result.get('connection_type') or result.get('end_connection') or '').lower()
    if requested_connection:
        if requested_connection in product_connection or product_connection in requested_connection:
            score += 0.05
            matched_fields.append('endConnection')
    else:
        score += 0.05
    
    # Determine tier
    if score >= 0.9:
        tier = 1
    elif score >= 0.7:
        tier = 2
    elif score >= 0.5:
        tier = 3
    else:
        tier = 4
    
    return (round(score, 2), tier)


def search_jsonb_tiered(
    normalized_specs: Dict,
    component_type: Optional[str] = None,
    max_results: int = 10,
    relax_constraints: bool = False  # Default to False - let LLM handle relaxation at application level
) -> List[Dict]:
    """
    Search products using tiered relaxation strategy.
    
    Args:
        normalized_specs: Normalized specs (size, valveType, material, pressureRating, endConnection, seatMaterial)
        component_type: Optional component type to narrow search
        max_results: Maximum results to return
        relax_constraints: If True, relax constraints if no matches found
    
    Returns:
        List of matching products with scores and tiers
    """
    print(f"🔍 search_jsonb_tiered called with: {normalized_specs}, component_type={component_type}", flush=True)
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all component tables
        component_tables = get_component_tables(conn)
        print(f"📊 get_component_tables returned {len(component_tables)} tables", flush=True)
        
        if not component_tables:
            print("⚠️ No component tables found. Make sure you've crawled products.")
            print("   Looking for tables with pattern: %_specs (excluding valve_specs)")
            # Debug: check what tables actually exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%spec%'
                ORDER BY table_name
            """)
            all_spec_tables = [row['table_name'] for row in cursor.fetchall()]
            print(f"   Found these spec tables: {all_spec_tables}")
            return []
        
        print(f"🔍 Found {len(component_tables)} component tables: {component_tables[:5]}", flush=True)
        
        # Build UNION query
        union_query = build_union_query(component_tables)
        if not union_query:
            return []
        
        # Extract search criteria
        size = normalize_size(normalized_specs.get('size'))
        valve_type = normalized_specs.get('valveType')
        material = normalized_specs.get('material')
        seat_material = normalized_specs.get('seatMaterial')
        pressure = normalized_specs.get('pressureRating')
        connection = normalized_specs.get('endConnection')
        
        # Build query with conditions
        query = f"""
            SELECT * FROM (
                {union_query}
            ) AS all_products
            WHERE 1=1
        """
        
        params = []
        conditions = []
        
        # Size match - EXACT match only (no partial matching to avoid "16" matching "6")
        if size:
            # Normalize the search size (remove quotes for comparison)
            size_normalized = normalize_size(size)
            # Match exact: "6", "6"", or '"6"'
            conditions.append("""
                (size = %s OR size = %s OR size = %s)
            """)
            params.extend([
                size_normalized,  # "6"
                f'{size_normalized}"',  # "6""
                f'"{size_normalized}"'  # '"6"'
            ])
        
        # Valve type match - exact or contains (for flexibility with valve type names)
        if valve_type:
            conditions.append("""
                (item ILIKE %s OR component_type ILIKE %s)
            """)
            params.extend([f'%{valve_type}%', f'%{valve_type}%'])
        
        # Pressure match - exact match on pressure number
        if pressure:
            pressure_num = extract_pressure_number(pressure)
            if pressure_num:
                conditions.append("""
                    (CAST(REGEXP_REPLACE(COALESCE(pressure_rating, pressure_class, ''), '[^0-9]', '', 'g') AS INTEGER) = %s)
                """)
                params.extend([pressure_num])
        
        # Material match - exact match (case-insensitive)
        if material:
            conditions.append("""
                (LOWER(body_material) = LOWER(%s))
            """)
            params.extend([material])
        
        # Seat material match - exact match (case-insensitive)
        if seat_material:
            conditions.append("""
                (LOWER(seat_material) = LOWER(%s))
            """)
            params.extend([seat_material])
        
        # Connection match - exact match (case-insensitive)
        if connection:
            conditions.append("""
                (LOWER(connection_type) = LOWER(%s)
                 OR LOWER(end_connection) = LOWER(%s)
                 OR LOWER(body_style) = LOWER(%s))
            """)
            params.extend([connection, connection, connection])
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += f" ORDER BY id DESC LIMIT {max_results * 3}"
        
        print(f"🔍 Executing query with {len(conditions)} conditions", flush=True)
        print(f"   Search criteria: size={size}, valve_type={valve_type}, seat_material={seat_material}, material={material}", flush=True)
        print(f"   Query (first 800 chars): {query[:800]}", flush=True)
        print(f"   Params ({len(params)}): {params}", flush=True)
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            print(f"   ✅ Found {len(results)} results", flush=True)
        except Exception as e:
            print(f"   ❌ Query execution error: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        if len(results) == 0:
            print("⚠️ No results found. Checking if tables have data...")
            # Quick check: count total rows in component tables
            for table in component_tables[:3]:
                try:
                    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE tech_specs IS NOT NULL")
                    cnt = cursor.fetchone()['cnt']
                    print(f"   {table}: {cnt} rows with tech_specs")
                except Exception as e:
                    print(f"   {table}: Error - {e}")
        
        # Calculate scores and sort
        scored_results = []
        for result in results:
            score, tier = calculate_score(dict(result), normalized_specs)
            result_dict = dict(result)
            result_dict['score'] = score
            result_dict['tier'] = tier
            result_dict['matched_fields'] = []  # Could enhance this
            scored_results.append(result_dict)
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top results
        return scored_results[:max_results]
        
    finally:
        cursor.close()
        conn.close()

