#!/usr/bin/env python3
"""
Analyze valve types and their spec structures in the database.
This script investigates what specs are present for different valve types
to understand if we need type-specific spec structures.
"""

import psycopg2
import json
import os
from collections import defaultdict
from typing import Dict, List, Set, Any
from urllib.parse import quote_plus

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(parent_env):
                load_dotenv(parent_env)
    except ImportError:
        pass
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    password = os.getenv('DB_PASSWORD', 'valve@123')
    encoded_password = quote_plus(password)
    
    pooler_host = os.getenv('DB_POOLER_HOST')
    if pooler_host:
        pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
        pooler_port = os.getenv('DB_POOLER_PORT', '6543')
        conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
        try:
            return psycopg2.connect(conn_string)
        except Exception as e:
            print(f"⚠️  Pooler connection failed: {e}")
            print("Trying direct connection...")
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db.deaohsesihodomvhqlxe.supabase.co'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=password,
        sslmode=os.getenv('DB_SSLMODE', 'require')
    )

def get_all_keys(obj: Any, prefix: str = "") -> Set[str]:
    """Recursively get all keys from a nested dictionary."""
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            if isinstance(value, (dict, list)):
                keys.update(get_all_keys(value, full_key))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(get_all_keys(item, prefix))
    return keys

def analyze_spec_structure(spec: Dict) -> Dict[str, Any]:
    """Analyze the structure of a spec JSONB object."""
    if not spec:
        return {}
    
    analysis = {
        'all_keys': get_all_keys(spec),
        'top_level_keys': set(spec.keys()) if isinstance(spec, dict) else set(),
        'has_materials': 'materials' in spec if isinstance(spec, dict) else False,
        'has_seat_material': False,
        'has_disc_material': False,
        'has_stem_material': False,
        'has_ball_material': False,
        'has_seal_material': False,
        'materials_structure': {},
    }
    
    # Check materials structure
    if isinstance(spec, dict) and 'materials' in spec:
        materials = spec['materials']
        if isinstance(materials, dict):
            analysis['materials_structure'] = {
                'keys': set(materials.keys()),
                'has_body_material': 'bodyMaterial' in materials,
                'has_seat_material': 'seatMaterial' in materials,
                'has_disc_material': 'discMaterial' in materials,
                'has_stem_material': 'stemMaterial' in materials,
                'has_ball_material': 'ballMaterial' in materials,
                'has_seal_material': 'sealMaterial' in materials,
            }
            analysis['has_seat_material'] = 'seatMaterial' in materials
            analysis['has_disc_material'] = 'discMaterial' in materials
            analysis['has_stem_material'] = 'stemMaterial' in materials
            analysis['has_ball_material'] = 'ballMaterial' in materials
            analysis['has_seal_material'] = 'sealMaterial' in materials
    
    # Check for seat material in other locations
    if not analysis['has_seat_material']:
        all_keys_str = ' '.join(analysis['all_keys']).lower()
        if 'seat' in all_keys_str:
            analysis['has_seat_material'] = True
    
    return analysis

def get_valve_types_with_samples(conn, samples_per_type: int = 3) -> Dict[str, List[Dict]]:
    """Get all valve types with sample records for each."""
    cursor = conn.cursor()
    
    # Get distinct valve types with counts
    cursor.execute("""
        SELECT valve_type, COUNT(*) as count
        FROM valve_specs
        WHERE valve_type IS NOT NULL
        GROUP BY valve_type
        ORDER BY count DESC
    """)
    
    valve_types = cursor.fetchall()
    
    result = {}
    for valve_type, count in valve_types:
        # Get sample records for this valve type
        cursor.execute("""
            SELECT 
                id, source_url, spec_sheet_url, sku,
                valve_type, size_nominal, body_material,
                spec, raw_specs
            FROM valve_specs
            WHERE valve_type = %s
            ORDER BY extracted_at DESC
            LIMIT %s
        """, (valve_type, samples_per_type))
        
        samples = []
        for row in cursor.fetchall():
            samples.append({
                'id': row[0],
                'source_url': row[1],
                'spec_sheet_url': row[2],
                'sku': row[3],
                'valve_type': row[4],
                'size_nominal': row[5],
                'body_material': row[6],
                'spec': row[7],
                'raw_specs': row[8],
            })
        
        result[valve_type] = {
            'count': count,
            'samples': samples
        }
    
    cursor.close()
    return result

def analyze_valve_type_specs():
    """Main analysis function."""
    print("=" * 80)
    print("Valve Type Spec Structure Analysis")
    print("=" * 80)
    print()
    
    conn = get_db_connection()
    
    # Get valve types with samples
    print("📊 Fetching valve types and samples...")
    valve_types_data = get_valve_types_with_samples(conn, samples_per_type=3)
    
    print(f"Found {len(valve_types_data)} distinct valve types\n")
    
    # Analyze each valve type
    analysis_results = {}
    all_spec_keys = defaultdict(int)  # Track frequency of spec keys across all types
    
    for valve_type, data in valve_types_data.items():
        print(f"🔍 Analyzing: {valve_type} ({data['count']} records)")
        
        type_analysis = {
            'count': data['count'],
            'samples_analyzed': len(data['samples']),
            'sample_urls': [],
            'spec_keys_found': set(),
            'materials_found': defaultdict(int),
            'has_seat_material': False,
            'has_disc_material': False,
            'has_stem_material': False,
            'has_ball_material': False,
            'has_seal_material': False,
            'sample_specs': []
        }
        
        for sample in data['samples']:
            type_analysis['sample_urls'].append(sample['source_url'])
            
            spec = sample.get('spec')
            if spec:
                spec_analysis = analyze_spec_structure(spec)
                type_analysis['spec_keys_found'].update(spec_analysis['all_keys'])
                
                # Track materials
                if spec_analysis['has_seat_material']:
                    type_analysis['has_seat_material'] = True
                if spec_analysis['has_disc_material']:
                    type_analysis['has_disc_material'] = True
                if spec_analysis['has_stem_material']:
                    type_analysis['has_stem_material'] = True
                if spec_analysis['has_ball_material']:
                    type_analysis['has_ball_material'] = True
                if spec_analysis['has_seal_material']:
                    type_analysis['has_seal_material'] = True
                
                # Store a sample spec structure (first one)
                if not type_analysis['sample_specs']:
                    type_analysis['sample_specs'].append({
                        'url': sample['source_url'],
                        'spec_structure': json.dumps(spec, indent=2),
                        'spec_keys': sorted(spec_analysis['all_keys']),
                        'materials_structure': spec_analysis['materials_structure']
                    })
                
                # Track all keys across all types
                for key in spec_analysis['all_keys']:
                    all_spec_keys[key] += 1
        
        analysis_results[valve_type] = type_analysis
        print(f"   ✓ Analyzed {len(data['samples'])} samples")
        print(f"   - Spec keys found: {len(type_analysis['spec_keys_found'])}")
        if type_analysis['has_seat_material']:
            print(f"   - ⚠️  Has seat material!")
        if type_analysis['has_disc_material']:
            print(f"   - ⚠️  Has disc material!")
        print()
    
    conn.close()
    
    # Generate report
    print("\n" + "=" * 80)
    print("ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    # Group valve types by common characteristics
    print("📋 Valve Types by Material Requirements:")
    print("-" * 80)
    
    seat_material_types = []
    disc_material_types = []
    stem_material_types = []
    ball_material_types = []
    
    for valve_type, analysis in analysis_results.items():
        if analysis['has_seat_material']:
            seat_material_types.append(valve_type)
        if analysis['has_disc_material']:
            disc_material_types.append(valve_type)
        if analysis['has_stem_material']:
            stem_material_types.append(valve_type)
        if analysis['has_ball_material']:
            ball_material_types.append(valve_type)
    
    if seat_material_types:
        print(f"\n✅ Types with SEAT MATERIAL ({len(seat_material_types)}):")
        for vtype in sorted(seat_material_types):
            print(f"   - {vtype}")
    
    if disc_material_types:
        print(f"\n✅ Types with DISC MATERIAL ({len(disc_material_types)}):")
        for vtype in sorted(disc_material_types):
            print(f"   - {vtype}")
    
    if stem_material_types:
        print(f"\n✅ Types with STEM MATERIAL ({len(stem_material_types)}):")
        for vtype in sorted(stem_material_types):
            print(f"   - {vtype}")
    
    if ball_material_types:
        print(f"\n✅ Types with BALL MATERIAL ({len(ball_material_types)}):")
        for vtype in sorted(ball_material_types):
            print(f"   - {vtype}")
    
    # Show sample specs for key valve types
    print("\n" + "=" * 80)
    print("SAMPLE SPEC STRUCTURES")
    print("=" * 80)
    
    # Focus on common valve types
    key_types = ['Butterfly Valve', 'Ball Valve', 'Gate Valve', 'Check Valve', 'Globe Valve']
    
    for valve_type in key_types:
        if valve_type in analysis_results:
            analysis = analysis_results[valve_type]
            if analysis['sample_specs']:
                sample = analysis['sample_specs'][0]
                print(f"\n📄 {valve_type} - Sample Spec Structure:")
                print(f"   URL: {sample['url']}")
                print(f"   Keys found: {len(sample['spec_keys'])}")
                print(f"   Materials structure: {json.dumps(sample['materials_structure'], indent=6)}")
                print(f"\n   Full spec structure:")
                print("   " + "\n   ".join(sample['spec_structure'].split('\n')[:30]))
                if len(sample['spec_structure'].split('\n')) > 30:
                    print("   ... (truncated)")
    
    # Save detailed report to JSON
    report_file = os.path.join(os.path.dirname(__file__), 'valve_type_spec_analysis.json')
    report_data = {
        'summary': {
            'total_valve_types': len(analysis_results),
            'types_with_seat_material': len(seat_material_types),
            'types_with_disc_material': len(disc_material_types),
            'types_with_stem_material': len(stem_material_types),
            'types_with_ball_material': len(ball_material_types),
        },
        'valve_types': {
            vtype: {
                'count': data['count'],
                'sample_urls': data['sample_urls'][:3],
                'spec_keys': sorted(list(data['spec_keys_found'])),
                'has_seat_material': data['has_seat_material'],
                'has_disc_material': data['has_disc_material'],
                'has_stem_material': data['has_stem_material'],
                'has_ball_material': data['has_ball_material'],
                'sample_spec': data['sample_specs'][0] if data['sample_specs'] else None
            }
            for vtype, data in analysis_results.items()
        },
        'all_spec_keys_frequency': dict(sorted(all_spec_keys.items(), key=lambda x: x[1], reverse=True))
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n✅ Detailed report saved to: {report_file}")
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("Based on the analysis:")
    print()
    print("1. VALVE-SPECIFIC MATERIAL FIELDS:")
    if seat_material_types:
        print(f"   - Consider adding 'seatMaterial' field for: {', '.join(seat_material_types[:5])}")
    if disc_material_types:
        print(f"   - Consider adding 'discMaterial' field for: {', '.join(disc_material_types[:5])}")
    if ball_material_types:
        print(f"   - Consider adding 'ballMaterial' field for: {', '.join(ball_material_types[:5])}")
    print()
    print("2. SEARCH IMPROVEMENTS:")
    print("   - For Butterfly Valves: Search by seat material instead of/in addition to body material")
    print("   - For Ball Valves: Consider ball material and seat material")
    print("   - For Check Valves: Consider disc material")
    print()
    print("3. DATABASE SCHEMA:")
    print("   - Current: Only 'body_material' is denormalized")
    print("   - Consider: Adding type-specific material columns OR")
    print("   - Consider: Using JSONB queries for valve-specific materials")
    print()

if __name__ == "__main__":
    analyze_valve_type_specs()

