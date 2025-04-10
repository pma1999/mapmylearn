#!/usr/bin/env python3
"""
Migration runner script for applying database migrations in the correct order.
"""

import os
import sys
import importlib.util
import time

def import_module_from_file(file_path):
    """Import a module from a file path."""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_migrations():
    """Run all migrations in the migrations directory in the correct order."""
    print("Running database migrations...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Migrations directory
    migrations_dir = os.path.join(script_dir, 'migrations')
    
    # Check if migrations directory exists
    if not os.path.exists(migrations_dir):
        print(f"Migrations directory not found: {migrations_dir}")
        return False
    
    # Get all Python files in the migrations directory
    migration_files = [
        f for f in os.listdir(migrations_dir) 
        if f.endswith('.py') and not f.startswith('__') 
        and f != 'env.py' and not f.startswith('alembic')
    ]
    
    # Sort migration files to ensure they're applied in the correct order
    migration_files.sort()
    
    print(f"Found {len(migration_files)} migrations: {', '.join(migration_files)}")
    
    # Run each migration
    for migration_file in migration_files:
        print(f"\nApplying migration: {migration_file}")
        start_time = time.time()
        
        try:
            file_path = os.path.join(migrations_dir, migration_file)
            migration_module = import_module_from_file(file_path)
            
            # Check if the module has an apply_migration function
            if hasattr(migration_module, 'apply_migration'):
                migration_module.apply_migration()
                elapsed_time = time.time() - start_time
                print(f"Migration {migration_file} completed successfully in {elapsed_time:.2f} seconds")
            else:
                print(f"Warning: Migration {migration_file} does not have an apply_migration function")
                
        except Exception as e:
            print(f"Error applying migration {migration_file}: {e}")
            return False
    
    print("\nAll migrations completed successfully")
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1) 