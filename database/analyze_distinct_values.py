#!/usr/bin/env python3
"""
Analyze distinct values in valve_specs table to identify compatibility mappings needed.
This helps ensure we don't miss any variations when searching.
"""

import psycopg2
import os
import json
from collections import Counter
from typing import Dict, List, Any
from urllib.parse import quote_plus

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Otherwise use individual environment variables
    password = os.getenv('DB_PASSWORD', 'valve@123')
    
    # URL encode password if needed
    encoded_password = quote_plus(password)
    
    # Try connection pooler first (if pooler host is set)
    pooler_host = os.getenv('DB_POOLER_HOST')
    if pooler_host:
        pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
        pooler_port = os.getenv('DB_POOLER_PORT', '5432')
        conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
        try:
            return psycopg2.connect(conn_string)
        except Exception as e:
            print(f"⚠️  Pooler connection failed: {e}")
            print("Trying direct connection...")
    
    # Fall back to direct connection
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'aws-1-us-east-2.pooler.supabase.com'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres.deaohsesihodomvhqlxe'),
        password=password,
        sslmode=os.getenv('DB_SSLMODE', 'require')
    )

def analyze_distinct_values():
    """Analyze distinct values for each searchable column."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Columns to analyze
        columns = [
            'valve_type',
            'size_nominal',
            'body_material',
            'pressure_class',
            'end_connection_inlet',
            'end_connection_outlet',
        ]
        
        results = {}
        
        for column in columns:
            print(f"\n{'='*60}")
            print(f"Analyzing: {column}")
            print('='*60)
            
            # Get distinct values with counts
            query = f"""
                SELECT {column}, COUNT(*) as count
                FROM valve_specs
                WHERE {column} IS NOT NULL
                GROUP BY {column}
                ORDER BY count DESC, {column}
                LIMIT 100
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            values = []
            for value, count in rows:
                values.append({
                    'value': value,
                    'count': count
                })
            
            results[column] = values
            
            # Print top 20
            print(f"Total distinct values: {len(values)}")
            print(f"\nTop 20 values:")
            for i, item in enumerate(values[:20], 1):
                print(f"  {i:2d}. {item['value']:40s} ({item['count']:5d} records)")
            
            if len(values) > 20:
                print(f"  ... and {len(values) - 20} more")
        
        # Save to JSON file
        output_file = 'distinct_values_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")
        print('='*60)
        
        # Generate compatibility suggestions
        print("\n\nCOMPATIBILITY MAPPING SUGGESTIONS:")
        print("="*60)
        generate_compatibility_suggestions(results)
        
        return results
        
    finally:
        cursor.close()
        conn.close()

def generate_compatibility_suggestions(results: Dict[str, List[Dict]]):
    """Generate compatibility mapping suggestions based on distinct values."""
    
    # Material compatibility
    print("\n1. MATERIAL COMPATIBILITY:")
    print("-" * 60)
    materials = [item['value'].lower() for item in results.get('body_material', [])]
    
    # Group similar materials (more precise matching)
    material_groups = {}
    for material in materials:
        key = None
        material_lower = material.lower()
        
        # Check in order of specificity
        if 'stainless' in material_lower or material_lower in ['ss', 's.s.'] or '316' in material_lower or '304' in material_lower:
            key = 'stainless_steel'
        elif 'carbon' in material_lower and 'steel' in material_lower:
            key = 'carbon_steel'
        elif 'forged' in material_lower and 'steel' in material_lower:
            key = 'carbon_steel'  # Forged steel is typically carbon steel
        elif material_lower in ['cs', 'c.s.']:
            key = 'carbon_steel'
        elif 'brass' in material_lower and 'stainless' not in material_lower:
            key = 'brass'
        elif 'bronze' in material_lower:
            key = 'bronze'
        elif ('cast iron' in material_lower or 'ductile iron' in material_lower) and 'steel' not in material_lower:
            key = 'cast_iron'
        elif 'pvc' in material_lower or 'cpvc' in material_lower:
            key = 'plastic'
        elif 'aluminum' in material_lower or 'aluminium' in material_lower:
            key = 'aluminum'
        
        if key:
            if key not in material_groups:
                material_groups[key] = []
            material_groups[key].append(material)
    
    for group, values in material_groups.items():
        print(f"\n  {group.upper().replace('_', ' ')}:")
        unique_values = sorted(set(values))
        print(f"    {unique_values[:10]}")
        if len(unique_values) > 10:
            print(f"    ... and {len(unique_values) - 10} more variations")
    
    # Valve type compatibility
    print("\n2. VALVE TYPE COMPATIBILITY:")
    print("-" * 60)
    valve_types = [item['value'].lower() for item in results.get('valve_type', [])]
    unique_valve_types = sorted(set(valve_types))
    print(f"  Found {len(unique_valve_types)} distinct valve types")
    print(f"  Top 10: {unique_valve_types[:10]}")
    
    # End connection compatibility
    print("\n3. END CONNECTION COMPATIBILITY:")
    print("-" * 60)
    inlet_connections = [item['value'].lower() for item in results.get('end_connection_inlet', [])]
    outlet_connections = [item['value'].lower() for item in results.get('end_connection_outlet', [])]
    all_connections = sorted(set(inlet_connections + outlet_connections))
    
    # Group similar connections
    connection_groups = {}
    for conn in all_connections:
        key = None
        if 'socket' in conn or 'sw' in conn or 'swe' in conn:
            key = 'socket_weld'
        elif 'threaded' in conn or 'npt' in conn or 'thread' in conn or 'screwed' in conn:
            key = 'threaded'
        elif 'flanged' in conn or 'flange' in conn or 'flg' in conn:
            key = 'flanged'
        elif 'butt' in conn or 'bwe' in conn:
            key = 'butt_weld'
        elif 'welded' in conn:
            key = 'welded'
        
        if key:
            if key not in connection_groups:
                connection_groups[key] = []
            connection_groups[key].append(conn)
    
    for group, values in connection_groups.items():
        print(f"\n  {group.upper().replace('_', ' ')}:")
        unique_values = sorted(set(values))
        print(f"    {unique_values[:10]}")
        if len(unique_values) > 10:
            print(f"    ... and {len(unique_values) - 10} more variations")
    
    # Pressure class compatibility
    print("\n4. PRESSURE CLASS COMPATIBILITY:")
    print("-" * 60)
    pressure_classes = [item['value'] for item in results.get('pressure_class', [])]
    unique_pressures = sorted(set(pressure_classes), key=lambda x: (len(str(x)), str(x)))
    print(f"  Found {len(unique_pressures)} distinct pressure classes")
    print(f"  Values: {unique_pressures[:20]}")
    if len(unique_pressures) > 20:
        print(f"  ... and {len(unique_pressures) - 20} more")
    
    # Size compatibility
    print("\n5. SIZE COMPATIBILITY:")
    print("-" * 60)
    sizes = [item['value'] for item in results.get('size_nominal', [])]
    
    def size_sort_key(x):
        """Sort sizes numerically where possible."""
        try:
            # Handle fractions like "1/2", "3/4"
            if '/' in x:
                parts = x.replace('"', '').split('/')
                if len(parts) == 2 and parts[0].replace('-', '').replace('.', '').isdigit() and parts[1].isdigit():
                    return float(parts[0]) / float(parts[1])
            # Handle mixed like "1-1/2", "2-1/2"
            if '-' in x and '/' in x:
                whole, frac = x.split('-', 1)
                if whole.replace('.', '').isdigit():
                    frac_parts = frac.split('/')
                    if len(frac_parts) == 2 and frac_parts[0].isdigit() and frac_parts[1].isdigit():
                        return float(whole) + (float(frac_parts[0]) / float(frac_parts[1]))
            # Handle simple numbers
            clean = x.replace('"', '').replace(' ', '').split()[0] if x.split() else x.replace('"', '')
            if clean.replace('.', '').isdigit():
                return float(clean)
        except:
            pass
        return 999  # Put non-numeric at end
    
    unique_sizes = sorted(set(sizes), key=size_sort_key)
    print(f"  Found {len(unique_sizes)} distinct sizes")
    print(f"  Top 20: {unique_sizes[:20]}")
    if len(unique_sizes) > 20:
        print(f"  ... and {len(unique_sizes) - 20} more")

if __name__ == "__main__":
    print("Analyzing distinct values in valve_specs table...")
    print("This will help identify compatibility mappings needed for search.")
    print()
    
    results = analyze_distinct_values()
    
    print("\n\nAnalysis complete!")
    print("Review the distinct_values_analysis.json file for full details.")

