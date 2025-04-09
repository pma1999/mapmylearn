import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_database():
    """Verifica la conexión a la base de datos y lista las tablas existentes"""
    # Obtener la URL de la base de datos desde la variable de entorno
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No se encontró la variable de entorno DATABASE_URL")
        sys.exit(1)
    
    print(f"Conectando a la base de datos...")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Listar las tablas en la base de datos
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
        """)
        
        tables = cursor.fetchall()
        print("\nTablas existentes en la base de datos:")
        for table in tables:
            print(f" - {table[0]}")
        
        # Verificar si existen las tablas principales
        expected_tables = ['users', 'sessions', 'learning_paths', 'credit_transactions', 'alembic_version']
        missing_tables = [table for table in expected_tables if (table,) not in tables]
        
        if missing_tables:
            print(f"\nTablas que faltan: {', '.join(missing_tables)}")
        else:
            print("\nTodas las tablas principales están presentes.")
            
        # Verificar la estructura de las tablas principales
        if ('users',) in tables:
            cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users';
            """)
            
            columns = cursor.fetchall()
            print("\nEstructura de la tabla 'users':")
            for column in columns:
                print(f" - {column[0]}: {column[1]}")
                
        if ('credit_transactions',) in tables:
            cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'credit_transactions';
            """)
            
            columns = cursor.fetchall()
            print("\nEstructura de la tabla 'credit_transactions':")
            for column in columns:
                print(f" - {column[0]}: {column[1]}")
        
        cursor.close()
        conn.close()
        print("\nVerificación completada con éxito")
        
    except Exception as e:
        print(f"ERROR durante la verificación: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_database() 