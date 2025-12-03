#!/usr/bin/env python3
"""
Comprehensive compatibility mappings based on actual database distinct values analysis.
This ensures we don't miss any variations when searching.
"""

# Material Compatibility Mapping
# Based on analysis of 100 distinct material values in database
MATERIAL_COMPATIBILITY = {
    # Carbon Steel variations
    'carbon steel': [
        'Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.',
        'Carbon Steel ASTM', 'ASTM A105 Carbon Steel'
    ],
    'cs': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
    'c.s.': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
    'forged steel': ['Forged Steel', 'Forged Carbon Steel', 'Carbon Steel'],
    'forged carbon steel': ['Forged Carbon Steel', 'Forged Steel', 'Carbon Steel'],
    
    # Stainless Steel variations
    'stainless steel': [
        'Stainless Steel', 'SS', 'S.S.', '316SS', '304SS', '316 Stainless Steel',
        '304 Stainless Steel', '316L', '316L Steel', '304', '316'
    ],
    'ss': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
    's.s.': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
    '316': ['316 Stainless Steel', '316SS', '316L', '316L Steel', 'Stainless Steel'],
    '304': ['304 Stainless Steel', '304SS', 'Stainless Steel'],
    '316ss': ['316 Stainless Steel', '316SS', 'Stainless Steel'],
    '304ss': ['304 Stainless Steel', '304SS', 'Stainless Steel'],
    '316l': ['316L Stainless Steel', '316L', '316L Steel', 'Stainless Steel'],
    
    # Brass variations (28 distinct values found)
    'brass': [
        'Brass', 'BR', 'Brass C37700', 'Brass - C37700', 'Brass C35330',
        'Brass CW617N', 'Brass - CW617N', '360 Brass', 'Lead-Free Brass',
        'Lead Free Brass', 'Lead-Free Brass - C46500', 'Lead-Free Brass - C27453',
        'Dezincification Resistant Lead-Free Brass', 'Brass /Nickel Plated',
        '2D Series Valve Body: Brass', '2V Series Valve Body: Brass'
    ],
    'br': ['Brass', 'BR'],
    'lead-free brass': ['Lead-Free Brass', 'Lead Free Brass', 'Brass'],
    
    # Bronze variations (11 distinct values found)
    'bronze': [
        'Bronze', 'BRZ', 'Bronze C84400', 'Bronze (C84400)', 'B584 Bronze',
        'B584 C84400 Bronze Alloy', 'B584-C84400 Bronze', 'Cast Bronze - C89844',
        'Lead-Free Bronze', 'Lead Free Bronze', 'C89836 Lead-Free Bronze',
        'Lead-Free Bronze - C89836'
    ],
    'brz': ['Bronze', 'BRZ'],
    'lead-free bronze': ['Lead-Free Bronze', 'Lead Free Bronze', 'Bronze'],
    
    # Cast Iron / Ductile Iron variations (13 distinct values found)
    'cast iron': [
        'Cast Iron', 'CI', 'Cast Iron (ASTM A126 Cl B)', 'Cast Iron - ASTM A126 B',
        'Cast Iron Body ASTM A126', 'Cast Iron, Epoxy Coated', 'Epoxy Coated Cast Iron'
    ],
    'ci': ['Cast Iron', 'CI'],
    'ductile iron': [
        'Ductile Iron', 'Ductile Iron - Epoxy Coated', 'Ductile Iron ASTM A536',
        'Ductile Iron Body with Epoxy Coating', 'Ductile Iron with Epoxy Coating',
        'Epoxy Coated Ductile Iron'
    ],
    'epoxy coated ductile iron': [
        'Epoxy Coated Ductile Iron', 'Ductile Iron - Epoxy Coated',
        'Ductile Iron with Epoxy Coating', 'Ductile Iron'
    ],
    
    # Plastic variations
    'pvc': ['PVC', 'PVC Body', 'PVC-Acrylic', 'UPVC'],
    'cpvc': ['CPVC', 'CPVC Body'],
    'plastic': ['PVC', 'CPVC', 'PVC Body', 'CPVC Body', 'UPVC'],
    
    # Aluminum variations
    'aluminum': [
        'Aluminum', 'Anodized Aluminum', 'Aluminum (Anodized)',
        'Extruded Aluminum', 'Diecast Aluminum Alloy, Irridite and Baked Epoxy Finish'
    ],
    'aluminium': ['Aluminum', 'Aluminium', 'Anodized Aluminum'],
}

# End Connection Compatibility Mapping
# Based on analysis of 86 distinct connection values in database
END_CONNECTION_COMPATIBILITY = {
    # Socket-weld variations
    'socket-weld': [
        'Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE',
        'Socket', 'Socket-Weld End', 'Socket Weld End'
    ],
    'sw': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
    'swe': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
    'socket weld': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
    'socket welded': ['Socket Welded', 'Socket-Weld', 'Socket Weld', 'SW', 'SWE'],
    
    # Threaded/NPT variations
    'threaded': [
        'Screwed/Threaded', 'Threaded', 'Thread', 'Screwed', 'THR',
        'NPT', 'NPT to ASME B1.20.1', 'Female NPT', 'FNPT', 'Male NPT', 'MNPT',
        'FNPT x MNPT', 'MNPT x FNPT', 'Clamp x Female NPT', 'Clamp x Male NPT',
        'Clamp x MNPT', 'NPT and Socket Ends Included'
    ],
    'npt': [
        'NPT', 'Female NPT', 'FNPT', 'Male NPT', 'MNPT', 'Screwed/Threaded',
        'FNPT x MNPT', 'MNPT x FNPT', 'NPT to ASME B1.20.1',
        'NPT and Socket Ends Included', 'Clamp x Female NPT', 'Clamp x Male NPT'
    ],
    'screwed': ['Screwed/Threaded', 'Threaded', 'Screwed', 'NPT'],
    'thr': ['Threaded', 'Screwed/Threaded', 'Screwed', 'THR'],
    
    # Flanged variations
    'flanged': [
        'Flanged', 'Flange', 'FLG', '150# Flange', 'ANSI Flange',
        'Square Flange x Square Flange', 'RF Flange', 'FF Flange'
    ],
    'flange': ['Flanged', 'Flange', 'FLG', '150# Flange', 'ANSI Flange'],
    'flg': ['Flanged', 'Flange', 'FLG'],
    '150#': ['150# Flange', 'Flanged', 'Flange'],
    
    # Butt-weld variations
    'butt-weld': [
        'Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE', 'Butt-Weld End',
        'Butt Weld End'
    ],
    'bwe': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
    'butt weld': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
    'butt welded': ['Butt Welded', 'Butt-Weld', 'Butt Weld', 'BWE'],
    
    # Clamp variations
    'clamp': [
        'Clamp', 'Tri-Clamp', 'Clamp x Female NPT', 'Clamp x Male NPT',
        'Clamp x MNPT', 'Tri-Clamp Connection'
    ],
    'tri-clamp': ['Tri-Clamp', 'Clamp', 'Tri-Clamp Connection'],
    
    # Other connection types
    'solder': ['Solder', 'Soldered'],
    'press connection': ['Press Connection', 'Pressfit', 'Press Fit'],
    'pressfit': ['Pressfit', 'Press Connection', 'Press Fit'],
}

# Valve Type Compatibility Mapping
# Based on analysis of 100 distinct valve types in database
# Note: Valve types use prefix matching, but we can add abbreviations
VALVE_TYPE_ABBREVIATIONS = {
    'gt': 'Gate Valve',
    'gl': 'Globe Valve',
    'bv': 'Ball Valve',
    'bfv': 'Butterfly Valve',
    'cv': 'Check Valve',
    'ch': 'Check Valve',
    'ndl': 'Needle Valve',
    'rv': 'Relief Valve',
    'ro': 'Restriction Orifice',
    'stt': 'Steam Trap',
    'str': 'Strainer',
    'thw': 'Three-Way Valve',
    '2w': '2-Way Ball Valve',
    '3w': '3-Way Ball Valve',
    '2wnc': '2-Way Normally Closed',
    '2wno': '2-Way Normally Open',
}

# Size Compatibility
# Sizes use exact match, but we should normalize input formats
SIZE_NORMALIZATION = {
    # Handle mixed number formats
    '1 1/2': '1-1/2',
    '1 1/4': '1-1/4',
    '2 1/2': '2-1/2',
    '3 1/2': '3-1/2',
    '4 1/2': '4-1/2',
    # Handle decimal equivalents (if needed)
    '0.5': '1/2',
    '0.75': '3/4',
    '0.25': '1/4',
    '1.5': '1-1/2',
    '2.5': '2-1/2',
}

def get_compatible_materials(material_input: str) -> list:
    """Get all compatible material values for a given input."""
    material_lower = material_input.lower().strip()
    return MATERIAL_COMPATIBILITY.get(material_lower, [material_input])

def get_compatible_end_connections(connection_input: str) -> list:
    """Get all compatible end connection values for a given input."""
    connection_lower = connection_input.lower().strip()
    return END_CONNECTION_COMPATIBILITY.get(connection_lower, [connection_input])

def normalize_valve_type(valve_type_input: str) -> str:
    """Normalize valve type input (expand abbreviations)."""
    valve_type_lower = valve_type_input.lower().strip()
    return VALVE_TYPE_ABBREVIATIONS.get(valve_type_lower, valve_type_input)

def normalize_size(size_input: str) -> str:
    """Normalize size input format."""
    size_clean = size_input.strip()
    return SIZE_NORMALIZATION.get(size_clean, size_clean)

if __name__ == "__main__":
    # Test the compatibility mappings
    print("Testing Material Compatibility:")
    print(f"  'cs' -> {get_compatible_materials('cs')}")
    print(f"  'stainless steel' -> {get_compatible_materials('stainless steel')}")
    print(f"  'brass' -> {get_compatible_materials('brass')[:5]}...")  # Show first 5
    
    print("\nTesting End Connection Compatibility:")
    print(f"  'sw' -> {get_compatible_end_connections('sw')}")
    print(f"  'npt' -> {get_compatible_end_connections('npt')[:5]}...")  # Show first 5
    print(f"  'flanged' -> {get_compatible_end_connections('flanged')}")
    
    print("\nTesting Valve Type Normalization:")
    print(f"  'gt' -> {normalize_valve_type('gt')}")
    print(f"  'bv' -> {normalize_valve_type('bv')}")
    
    print("\nTesting Size Normalization:")
    print(f"  '1 1/2' -> {normalize_size('1 1/2')}")
    print(f"  '0.5' -> {normalize_size('0.5')}")




