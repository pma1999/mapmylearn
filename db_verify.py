import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

def verify_database():
    """Verifica el estado actual de la base de datos"""
    print("Verificando el estado de la base de datos...")
    
    # Railway establece DATABASE_URL automáticamente en el ambiente
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No se encontró la variable de entorno DATABASE_URL")
        sys.exit(1)
    
    print("Conectando a la base de datos...")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Listar las tablas existentes
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\nTablas existentes en la base de datos:")
        for table in tables:
            print(f" - {table[0]}")
        
        # Verificar la versión actual de alembic
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        print(f"\nVersión actual de alembic: {version[0]}")
        
        # Verificar la estructura de cada tabla
        tables_to_check = ['users', 'sessions', 'learning_paths', 'credit_transactions', 'alembic_version']
        
        for table in tables_to_check:
            cursor.execute(f"""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table}'
            ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print(f"\nEstructura de la tabla '{table}':")
            for column in columns:
                print(f" - {column[0]}: {column[1]}, Default: {column[2]}, Nullable: {column[3]}")
            
            # Verificar índices
            cursor.execute(f"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = '{table}';
            """)
            
            indexes = cursor.fetchall()
            if indexes:
                print(f"\nÍndices de la tabla '{table}':")
                for idx in indexes:
                    print(f" - {idx[0]}: {idx[1]}")
        
        # Verificar usuarios en la tabla users
        cursor.execute("SELECT id, email, full_name, is_admin, credits FROM users;")
        users = cursor.fetchall()
        
        print("\nUsuarios registrados:")
        for user in users:
            print(f" - ID: {user[0]}, Email: {user[1]}, Nombre: {user[2]}, Admin: {user[3]}, Créditos: {user[4]}")
        
        # Cerrar la conexión
        cursor.close()
        conn.close()
        
        print("\nVerificación de la base de datos completada con éxito")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    verify_database() 