#!/usr/bin/env python3
"""
Search valve specs from the database by specifications.
"""

import psycopg2
import os
import json
from typing import Dict, List, Optional, Any
from psycopg2.extras import RealDictCursor

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try loading from current directory first, then parent directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try parent directory
        parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(parent_env):
            load_dotenv(parent_env)
except ImportError:
    # python-dotenv not installed, skip
    pass

# Import comprehensive compatibility mappings
try:
    from comprehensive_compatibility_mapping import (
        MATERIAL_COMPATIBILITY as COMPREHENSIVE_MATERIAL_COMPATIBILITY,
        END_CONNECTION_COMPATIBILITY as COMPREHENSIVE_END_CONNECTION_COMPATIBILITY,
        VALVE_TYPE_ABBREVIATIONS,
        normalize_size as comprehensive_normalize_size,
        normalize_valve_type as comprehensive_normalize_valve_type
    )
    USE_COMPREHENSIVE_MAPPINGS = True
except ImportError:
    # Fallback if comprehensive_compatibility_mapping.py is not available
    USE_COMPREHENSIVE_MAPPINGS = False
    COMPREHENSIVE_MATERIAL_COMPATIBILITY = None
    COMPREHENSIVE_END_CONNECTION_COMPATIBILITY = None
    VALVE_TYPE_ABBREVIATIONS = None
    comprehensive_normalize_size = None
    comprehensive_normalize_valve_type = None

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    password = os.getenv('DB_PASSWORD', 'valve@123')
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db.deaohsesihodomvhqlxe.supabase.co'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=password,
        sslmode=os.getenv('DB_SSLMODE', 'require')
    )

def search_specs(
    valve_type: Optional[str] = None,
    size_nominal: Optional[str] = None,
    body_material: Optional[str] = None,
    pressure_class: Optional[str] = None,
    end_connection: Optional[str] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search valve specs by various criteria.
    
    Args:
        valve_type: Type of valve (e.g., "Gate Valve", "Ball Valve")
        size_nominal: Nominal size (e.g., "1/2", "3/4", "1")
        body_material: Body material (e.g., "Carbon Steel", "Stainless Steel")
        pressure_class: Pressure class (e.g., "800", "150", "300")
        end_connection: End connection type (e.g., "Socket-weld", "NPT", "Threaded")
        max_results: Maximum number of results to return
    
    Returns:
        List of matching valve specs as dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Build dynamic WHERE clause
        conditions = []
        params = []
        
        # Material compatibility mapping (comprehensive - based on actual database analysis)
        # Use comprehensive mappings if available, otherwise use inline mappings
        if USE_COMPREHENSIVE_MAPPINGS:
            MATERIAL_COMPATIBILITY = COMPREHENSIVE_MATERIAL_COMPATIBILITY
        else:
            MATERIAL_COMPATIBILITY = {
            # Carbon Steel variations
            'carbon steel': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
            'cs': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
            'c.s.': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
            'forged steel': ['Forged Steel', 'Forged Carbon Steel', 'Carbon Steel'],
            'forged carbon steel': ['Forged Carbon Steel', 'Forged Steel', 'Carbon Steel'],
            
            # Stainless Steel variations
            'stainless steel': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS', '316 Stainless Steel', '304 Stainless Steel', '316L', '316L Steel', '316', '304'],
            'ss': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
            's.s.': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
            '316': ['316 Stainless Steel', '316SS', '316L', '316L Steel', 'Stainless Steel'],
            '304': ['304 Stainless Steel', '304SS', 'Stainless Steel'],
            '316l': ['316L Stainless Steel', '316L', '316L Steel', 'Stainless Steel'],
            
            # Brass variations (28 distinct values in database)
            'brass': ['Brass', 'BR', 'Brass C37700', 'Brass - C37700', 'Lead-Free Brass', 'Lead Free Brass', 'Brass C35330', 'Brass CW617N'],
            'br': ['Brass', 'BR'],
            'lead-free brass': ['Lead-Free Brass', 'Lead Free Brass', 'Brass'],
            
            # Bronze variations (11 distinct values in database)
            'bronze': ['Bronze', 'BRZ', 'Bronze C84400', 'Lead-Free Bronze', 'Lead Free Bronze', 'B584 Bronze'],
            'brz': ['Bronze', 'BRZ'],
            'lead-free bronze': ['Lead-Free Bronze', 'Lead Free Bronze', 'Bronze'],
            
            # Cast Iron / Ductile Iron variations
            'cast iron': ['Cast Iron', 'CI', 'Cast Iron (ASTM A126 Cl B)', 'Epoxy Coated Cast Iron'],
            'ci': ['Cast Iron', 'CI'],
            'ductile iron': ['Ductile Iron', 'Ductile Iron - Epoxy Coated', 'Epoxy Coated Ductile Iron'],
            'epoxy coated ductile iron': ['Epoxy Coated Ductile Iron', 'Ductile Iron - Epoxy Coated', 'Ductile Iron'],
            
            # Plastic variations
            'pvc': ['PVC', 'PVC Body', 'UPVC'],
            'cpvc': ['CPVC', 'CPVC Body'],
            
            # Aluminum variations
            'aluminum': ['Aluminum', 'Anodized Aluminum', 'Aluminum (Anodized)'],
            'aluminium': ['Aluminum', 'Aluminium', 'Anodized Aluminum'],
        }
        
        if valve_type:
            # Valve type compatibility mapping (for exact matches - faster than ILIKE)
            # Use IN clause with exact matches when we have mappings (can use index)
            # Fallback to ILIKE for unmapped inputs (slower but flexible)
            # Normalize valve type using comprehensive mappings if available
            if USE_COMPREHENSIVE_MAPPINGS and comprehensive_normalize_valve_type:
                normalized_valve_type = comprehensive_normalize_valve_type(valve_type)
                if normalized_valve_type != valve_type:
                    # If abbreviation was expanded, use the expanded form
                    valve_type = normalized_valve_type
            
            VALVE_TYPE_COMPATIBILITY = {
                # Abbreviations
                'gt': ['Gate Valve', 'Gate Valve (Non-Rising Stem)', 'Gate Valve (Rising Stem)'],
                'gl': ['Globe Valve'],
                'bv': ['Ball Valve', '2-Piece Ball Valve', '3-Piece Ball Valve', 'Gas Ball Valve'],
                'bfv': ['Butterfly Valve', 'Butterfly Valves', 'High Performance Butterfly Valve'],
                'cv': ['Check Valve', 'Swing Check Valve', 'Silent Check Valve', 'Horizontal Swing Check Valve'],
                'ch': ['Check Valve', 'Swing Check Valve', 'Silent Check Valve'],
                'ndl': ['Needle Valve'],
                'rv': ['Relief Valve'],
                'ro': ['Restriction Orifice'],
                'stt': ['Steam Trap'],
                'str': ['Strainer', 'Y- Strainer'],
                'thw': ['3-Way Ball Valve', '3-Way Diverter Ball Valve', '3-Way Pneumatically Actuated Ball Valve', '3-Way Electrically Actuated Ball Valve'],
                '2w': ['2-Way Ball Valve', '2-Way Pneumatically Actuated Ball Valve', '2-Way Electrically Actuated Ball Valve', '2-Way Ball Valve (V-Port)'],
                '3w': ['3-Way Ball Valve', '3-Way Pneumatically Actuated Ball Valve', '3-Way Electrically Actuated Ball Valve', '3-Way Diverter Ball Valve'],
                '2wnc': ['2-Way Normally Closed'],
                '2wno': ['2-Way Normally Open'],
                
                # Common full names (normalized to lowercase for lookup)
                'ball valve': ['Ball Valve', '2-Piece Ball Valve', '3-Piece Ball Valve', 'Gas Ball Valve', '2-Way Ball Valve', '3-Way Ball Valve'],
                'gate valve': ['Gate Valve', 'Gate Valve (Non-Rising Stem)', 'Gate Valve (Rising Stem)'],
                'globe valve': ['Globe Valve'],
                'butterfly valve': ['Butterfly Valve', 'Butterfly Valves', 'High Performance Butterfly Valve', 'Pneumatically Actuated Butterfly Valve', 'Electrically Actuated Butterfly Valve'],
                'check valve': ['Check Valve', 'Swing Check Valve', 'Silent Check Valve', 'Horizontal Swing Check Valve'],
                'solenoid valve': ['Solenoid Valve'],
            }
            
            # Normalize input to lowercase for case-insensitive lookup
            # This allows "GT", "gt", "Gt" to all work the same way
            valve_type_lower = valve_type.lower().strip()
            compatible_types = VALVE_TYPE_COMPATIBILITY.get(valve_type_lower, None)
            
            if compatible_types:
                # Use IN clause with exact matches (FAST - can use index)
                # This is much faster than ILIKE because it can use the index
                placeholders = ','.join(['%s'] * len(compatible_types))
                conditions.append(f"valve_type IN ({placeholders})")
                params.extend(compatible_types)
            else:
                # Fallback to ILIKE for unmapped inputs (SLOWER but flexible)
                # This handles partial matches and unmapped valve types
                # ILIKE is case-insensitive, so "Gate", "GATE", "gate" all work
                conditions.append("valve_type ILIKE %s")
                params.append(f"{valve_type}%")
        
        if size_nominal:
            # Size normalization (handle format variations)
            if USE_COMPREHENSIVE_MAPPINGS and comprehensive_normalize_size:
                # Use comprehensive size normalization function
                normalized_size = comprehensive_normalize_size(size_nominal)
            else:
                # Use inline normalization
                SIZE_NORMALIZATION = {
                    '1 1/2': '1-1/2',
                    '1 1/4': '1-1/4',
                    '2 1/2': '2-1/2',
                    '3 1/2': '3-1/2',
                    '4 1/2': '4-1/2',
                    '0.5': '1/2',
                    '0.75': '3/4',
                    '0.25': '1/4',
                    '1.5': '1-1/2',
                    '2.5': '2-1/2',
                }
                normalized_size = SIZE_NORMALIZATION.get(size_nominal.strip(), size_nominal.strip())
            
            # Exact match for size (fastest) - try both original and normalized
            conditions.append("(size_nominal = %s OR size_nominal = %s)")
            params.append(size_nominal.strip())
            params.append(normalized_size)
        
        if body_material:
            # Fast material matching using compatibility list
            # Normalize to lowercase for case-insensitive lookup (CS, cs, Cs all work)
            material_lower = body_material.lower().strip()
            compatible_materials = MATERIAL_COMPATIBILITY.get(material_lower, [body_material])
            
            # Use IN clause with exact matches (can use index)
            placeholders = ','.join(['%s'] * len(compatible_materials))
            conditions.append(f"body_material IN ({placeholders})")
            params.extend(compatible_materials)
        
        if pressure_class:
            # Exact match (can use index) + allow NULL
            conditions.append("(pressure_class = %s OR pressure_class IS NULL)")
            params.append(pressure_class)
        
        if end_connection:
            # End connection compatibility mapping (based on 86 distinct values in database)
            # Use comprehensive mappings if available
            if USE_COMPREHENSIVE_MAPPINGS:
                END_CONNECTION_COMPATIBILITY = COMPREHENSIVE_END_CONNECTION_COMPATIBILITY
            else:
                END_CONNECTION_COMPATIBILITY = {
                # Socket-weld variations
                'socket-weld': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE', 'Socket'],
                'sw': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
                'swe': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
                'socket weld': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
                'socket welded': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
                
                # Threaded/NPT variations
                'threaded': ['Screwed/Threaded', 'Threaded', 'Thread', 'Screwed', 'THR', 'NPT', 'Female NPT', 'FNPT', 'Male NPT', 'MNPT'],
                'npt': ['NPT', 'Female NPT', 'FNPT', 'Male NPT', 'MNPT', 'Screwed/Threaded', 'NPT to ASME B1.20.1'],
                'screwed': ['Screwed/Threaded', 'Threaded', 'Screwed', 'NPT'],
                'thr': ['Threaded', 'Screwed/Threaded', 'Screwed', 'THR'],
                
                # Flanged variations
                'flanged': ['Flanged', 'Flange', 'FLG', '150# Flange', 'ANSI Flange'],
                'flange': ['Flanged', 'Flange', 'FLG', '150# Flange'],
                'flg': ['Flanged', 'Flange', 'FLG'],
                
                # Butt-weld variations
                'butt-weld': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
                'bwe': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
                'butt weld': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
                'butt welded': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
            }
            
            # Normalize to lowercase for case-insensitive lookup (SW, sw, Sw all work)
            connection_lower = end_connection.lower().strip()
            compatible_connections = END_CONNECTION_COMPATIBILITY.get(connection_lower, [end_connection])
            
            # Build OR condition for all compatible connections on both inlet and outlet
            connection_conditions = []
            for conn in compatible_connections:
                connection_conditions.append("(end_connection_inlet = %s OR end_connection_outlet = %s)")
                params.append(conn)
                params.append(conn)
            
            if connection_conditions:
                conditions.append(f"({' OR '.join(connection_conditions)})")
            else:
                # Fallback to original behavior if no compatibility mapping
                conditions.append("(end_connection_inlet = %s OR end_connection_outlet = %s OR (end_connection_inlet IS NULL AND end_connection_outlet IS NULL))")
                params.append(end_connection)
                params.append(end_connection)
        
        # Build query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
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
                end_connection_outlet,
                starting_price,
                msrp,
                savings,
                spec,
                price_info,
                extracted_at
            FROM valve_specs
            WHERE {where_clause}
            ORDER BY extracted_at DESC
            LIMIT %s
        """
        
        params.append(max_results)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to list of dicts
        return [dict(row) for row in results]
        
    finally:
        cursor.close()
        conn.close()

def search_specs_by_normalized_specs(normalized_specs: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search specs using normalized specification object.
    
    Args:
        normalized_specs: Dictionary with keys like:
            - size (or size_nominal)
            - valveType (or valve_type)
            - material (or body_material)
            - pressureRating (or pressure_class)
            - endConnection (or end_connection)
        max_results: Maximum number of results
    
    Returns:
        List of matching valve specs
    """
    return search_specs(
        valve_type=normalized_specs.get('valveType') or normalized_specs.get('valve_type'),
        size_nominal=normalized_specs.get('size') or normalized_specs.get('size_nominal'),
        body_material=normalized_specs.get('material') or normalized_specs.get('body_material'),
        pressure_class=normalized_specs.get('pressureRating') or normalized_specs.get('pressure_class'),
        end_connection=normalized_specs.get('endConnection') or normalized_specs.get('end_connection'),
        max_results=max_results
    )

if __name__ == "__main__":
    # Test the search function
    import sys
    
    if len(sys.argv) > 1:
        # Parse JSON input
        input_json = json.loads(sys.argv[1])
        results = search_specs_by_normalized_specs(input_json)
        print(json.dumps(results, indent=2, default=str))
    else:
        # Example search
        results = search_specs(
            valve_type="Gate Valve",
            size_nominal="1/2",
            body_material="Carbon Steel",
            pressure_class="800",
            end_connection="Socket-weld"
        )
        print(json.dumps(results, indent=2, default=str))

