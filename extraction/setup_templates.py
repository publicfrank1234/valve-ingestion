#!/usr/bin/env python3
"""
Setup script for template-based extraction system.

This script:
1. Creates the template database tables
2. Loads example templates
3. Verifies the setup
"""

import os
import sys
import psycopg2
from template_manager import TemplateManager
from example_templates import load_example_templates


def setup_database(db_connection_string: str):
    """Create template database tables."""
    print("Setting up database tables...")
    
    # Read schema SQL
    schema_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'database',
        'template_schema.sql'
    )
    
    if not os.path.exists(schema_path):
        print(f"✗ Schema file not found: {schema_path}")
        return False
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    try:
        conn = psycopg2.connect(db_connection_string)
        with conn.cursor() as cur:
            # Execute schema SQL
            cur.execute(schema_sql)
            conn.commit()
        conn.close()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        return False


def verify_setup(template_manager: TemplateManager):
    """Verify the setup by checking templates."""
    print("\nVerifying setup...")
    
    templates = template_manager.list_templates()
    print(f"✓ Found {len(templates)} templates in database")
    
    for template in templates:
        print(f"  - {template['template_id']}: {template['component_type']} ({template['category']})")
    
    return len(templates) > 0


def main():
    """Main setup function."""
    print("="*60)
    print("Template-Based Extraction System Setup")
    print("="*60)
    
    # Get database connection string
    db_conn_string = os.getenv("DATABASE_URL")
    if not db_conn_string:
        print("\n⚠️  DATABASE_URL environment variable not set")
        print("Please set it, for example:")
        print("  export DATABASE_URL='postgresql://user:password@localhost/valve_specs'")
        db_conn_string = input("\nEnter database connection string: ").strip()
        if not db_conn_string:
            print("✗ No database connection string provided")
            sys.exit(1)
    
    # Step 1: Setup database
    if not setup_database(db_conn_string):
        print("\n✗ Database setup failed")
        sys.exit(1)
    
    # Step 2: Load example templates
    print("\nLoading example templates...")
    template_manager = TemplateManager(db_conn_string)
    load_example_templates(template_manager)
    
    # Step 3: Verify setup
    if not verify_setup(template_manager):
        print("\n⚠️  Setup completed but no templates found")
    else:
        print("\n✓ Setup completed successfully!")
        print("\nYou can now use the template-based extraction system.")
        print("\nExample usage:")
        print("  from template_based_extractor import TemplateBasedExtractor")
        print("  extractor = TemplateBasedExtractor(db_conn_string)")
        print("  result = extractor.extract_from_url('https://valveman.com/products/...')")


if __name__ == "__main__":
    main()

