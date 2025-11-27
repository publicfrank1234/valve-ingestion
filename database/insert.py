#!/usr/bin/env python3
"""
Insert extracted valve specifications into PostgreSQL database.
"""

import json
import os
import psycopg2
from psycopg2.extras import Json, execute_values
from psycopg2 import sql
from typing import Dict, List, Optional
import sys

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    import sys
    import os
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, skip
    
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Get from environment variables (required)
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_sslmode = os.getenv('DB_SSLMODE', 'require')
    
    if not db_host or not db_password:
        raise ValueError(
            "Database credentials not found! Please set DB_HOST and DB_PASSWORD environment variables.\n"
            "Create a .env file with:\n"
            "  DB_HOST=db.your-project.supabase.co\n"
            "  DB_PASSWORD=your-password\n"
            "  DB_USER=postgres\n"
            "  DB_NAME=postgres\n"
            "  DB_PORT=5432\n"
            "  DB_SSLMODE=require"
        )
    
    # Try connection with IPv4 preference
    try:
        # Force IPv4 by using connection_factory or connection parameters
        return psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode=db_sslmode,
            connect_timeout=10
        )
    except psycopg2.OperationalError as e:
        # If IPv6 connection fails, try using connection pooler (port 6543)
        if "Network is unreachable" in str(e) or "IPv6" in str(e):
            print("⚠️  Direct connection failed (IPv6 issue). Trying connection pooler...")
            pooler_host = db_host.replace('.supabase.co', '.pooler.supabase.com')
            pooler_port = '6543'
            try:
                return psycopg2.connect(
                    host=pooler_host,
                    port=pooler_port,
                    database=db_name,
                    user=db_user,
                    password=db_password,
                    sslmode=db_sslmode,
                    connect_timeout=10
                )
            except Exception as pooler_error:
                raise ValueError(
                    f"Connection failed. Tried both direct and pooler.\n"
                    f"Direct error: {e}\n"
                    f"Pooler error: {pooler_error}\n\n"
                    f"Try using connection pooler in .env:\n"
                    f"  DB_HOST=db.deaohsesihodomvhqlxe.pooler.supabase.com\n"
                    f"  DB_PORT=6543"
                )
        else:
            raise

def insert_spec(conn, spec_data: Dict) -> Optional[int]:
    """Insert a single valve spec into the database."""
    cursor = conn.cursor()
    
    try:
        # Extract denormalized fields for easy querying
        spec = spec_data.get('spec', {})
        price_info = spec_data.get('priceInfo', {})
        
        valve_type = spec.get('valveType')
        size_obj = spec.get('size', {})
        size_nominal = size_obj.get('nominalSize') if isinstance(size_obj, dict) else None
        
        materials = spec.get('materials', {})
        body_material = materials.get('bodyMaterial') if isinstance(materials, dict) else None
        
        pressure_rating = spec.get('pressureRating', {})
        max_pressure = pressure_rating.get('maxOperatingPressure') if isinstance(pressure_rating, dict) else None
        pressure_unit = pressure_rating.get('pressureUnit') if isinstance(pressure_rating, dict) else None
        pressure_class = pressure_rating.get('pressureClass') if isinstance(pressure_rating, dict) else None
        
        temp_rating = spec.get('temperatureRating', {})
        max_temperature = temp_rating.get('maxTemperature') if isinstance(temp_rating, dict) else None
        temperature_unit = temp_rating.get('temperatureUnit') if isinstance(temp_rating, dict) else None
        
        end_connections = spec.get('endConnections', {})
        end_connection_inlet = end_connections.get('inlet') if isinstance(end_connections, dict) else None
        end_connection_outlet = end_connections.get('outlet') if isinstance(end_connections, dict) else None
        
        # Extract price info
        sku = price_info.get('sku')
        starting_price = price_info.get('startingPrice')
        msrp = price_info.get('msrp')
        savings = price_info.get('savings')
        
        # Parse extracted_at timestamp
        extracted_at = spec_data.get('extractedAt')
        if extracted_at and isinstance(extracted_at, str):
            from datetime import datetime
            try:
                extracted_at = datetime.fromisoformat(extracted_at.replace('Z', '+00:00'))
            except:
                extracted_at = None
        
        # Insert with ON CONFLICT to handle duplicates
        insert_query = """
            INSERT INTO valve_specs (
                source_url, spec_sheet_url, sku, extracted_at,
                starting_price, msrp, savings,
                valve_type, size_nominal, body_material,
                max_pressure, pressure_unit, pressure_class,
                max_temperature, temperature_unit,
                end_connection_inlet, end_connection_outlet,
                spec, raw_specs, price_info
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (source_url) 
            DO UPDATE SET
                spec_sheet_url = EXCLUDED.spec_sheet_url,
                sku = EXCLUDED.sku,
                extracted_at = EXCLUDED.extracted_at,
                starting_price = EXCLUDED.starting_price,
                msrp = EXCLUDED.msrp,
                savings = EXCLUDED.savings,
                valve_type = EXCLUDED.valve_type,
                size_nominal = EXCLUDED.size_nominal,
                body_material = EXCLUDED.body_material,
                max_pressure = EXCLUDED.max_pressure,
                pressure_unit = EXCLUDED.pressure_unit,
                pressure_class = EXCLUDED.pressure_class,
                max_temperature = EXCLUDED.max_temperature,
                temperature_unit = EXCLUDED.temperature_unit,
                end_connection_inlet = EXCLUDED.end_connection_inlet,
                end_connection_outlet = EXCLUDED.end_connection_outlet,
                spec = EXCLUDED.spec,
                raw_specs = EXCLUDED.raw_specs,
                price_info = EXCLUDED.price_info,
                updated_at = NOW()
            RETURNING id
        """
        
        cursor.execute(insert_query, (
            spec_data.get('sourceUrl'),
            spec_data.get('specSheetUrl'),
            sku,
            extracted_at,
            starting_price,
            msrp,
            savings,
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
            Json(spec),
            Json(spec_data.get('rawSpecs', {})),
            Json(price_info)
        ))
        
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else None
        
    except Exception as e:
        conn.rollback()
        print(f"Error inserting spec: {e}")
        return None
    finally:
        cursor.close()

def insert_specs_batch(conn, specs_list: List[Dict]) -> Dict:
    """Insert multiple specs in a batch."""
    results = {
        'inserted': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    for spec_data in specs_list:
        try:
            # Check if exists
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM valve_specs WHERE source_url = %s", (spec_data.get('sourceUrl'),))
            exists = cursor.fetchone()
            cursor.close()
            
            spec_id = insert_spec(conn, spec_data)
            if spec_id:
                if exists:
                    results['updated'] += 1
                else:
                    results['inserted'] += 1
            else:
                results['errors'] += 1
                results['error_details'].append({
                    'url': spec_data.get('sourceUrl'),
                    'error': 'Insert failed'
                })
        except Exception as e:
            results['errors'] += 1
            results['error_details'].append({
                'url': spec_data.get('sourceUrl'),
                'error': str(e)
            })
    
    return results

def main():
    """Main function to insert specs from JSON file."""
    if len(sys.argv) < 2:
        print("Usage: python insert_spec.py <specs_json_file>")
        print("Example: python insert_spec.py test_extracted_spec.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Load specs from JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Handle both single spec and list of specs
    if isinstance(data, dict):
        specs_list = [data]
    elif isinstance(data, list):
        specs_list = data
    else:
        print("Error: JSON must be an object or array")
        sys.exit(1)
    
    print(f"Loading {len(specs_list)} specs into database...")
    
    # Connect to database
    try:
        conn = get_db_connection()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        print("\nMake sure you have set these environment variables:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    # Insert specs
    results = insert_specs_batch(conn, specs_list)
    
    print(f"\n{'='*60}")
    print(f"Insert Results:")
    print(f"  Inserted: {results['inserted']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Errors: {results['errors']}")
    print(f"{'='*60}")
    
    if results['error_details']:
        print("\nErrors:")
        for error in results['error_details'][:5]:  # Show first 5 errors
            print(f"  - {error['url']}: {error['error']}")
    
    conn.close()

if __name__ == "__main__":
    main()

