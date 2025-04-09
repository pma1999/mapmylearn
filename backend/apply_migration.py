"""
Script para aplicar la migración de créditos directamente en PostgreSQL.
Este script evita problemas con Alembic y aplica la migración SQL directamente.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def execute_migration():
    """Ejecuta la migración para añadir la columna credits a la tabla users"""
    # Obtener la URL de la base de datos desde la variable de entorno
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No se encontró la variable de entorno DATABASE_URL")
        sys.exit(1)
    
    print(f"Usando base de datos: {db_url}")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'credits';
        """)
        
        if cursor.fetchone():
            print("La columna 'credits' ya existe en la tabla 'users'")
        else:
            # Añadir la columna credits
            print("Añadiendo columna 'credits' a la tabla 'users'...")
            cursor.execute("""
            ALTER TABLE users
            ADD COLUMN credits INTEGER NOT NULL DEFAULT 0;
            """)
            print("Columna añadida correctamente")
        
        # Crear un registro de migración en alembic_version
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        );
        """)
        
        if cursor.fetchone()[0]:
            # Verificar si la revisión ya existe
            cursor.execute("SELECT version_num FROM alembic_version;")
            current_version = cursor.fetchone()
            print(f"Versión actual en alembic_version: {current_version}")
            
            # Actualizar a nuestra nueva versión
            new_version = 'b10d49747884'  # ID de nuestra revisión
            
            if current_version and current_version[0] != new_version:
                cursor.execute("UPDATE alembic_version SET version_num = %s;", (new_version,))
                print(f"Actualizada alembic_version a {new_version}")
            else:
                print(f"La versión en alembic_version ya es {new_version}")
        else:
            print("La tabla alembic_version no existe, no se pudo actualizar la versión")
        
        cursor.close()
        conn.close()
        print("Migración completada con éxito")
        
    except Exception as e:
        print(f"ERROR durante la migración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    execute_migration() 