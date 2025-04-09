import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_connection():
    """Prueba simple de conexión a la base de datos PostgreSQL"""
    print("Probando conexión a PostgreSQL en Railway...")
    
    # Intentar obtener la URL desde las variables de entorno de Railway
    try:
        # Conectar a la base de datos usando railway para obtener la URL
        print("Conectando a la base de datos...")
        
        # Si la variable DATABASE_URL no está disponible, construimos la URL con las credenciales
        db_host = "containers-us-west-16.railway.app"  # Esto podría variar según tu configuración
        db_port = "6316"  # El puerto suele ser un puerto aleatorio en Railway
        db_name = "railway"
        db_user = "postgres"
        db_password = "LaiaTrilla170214!"  # Contraseña obtenida del archivo .env
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        print(f"Usando URL de conexión (host/puerto parcialmente ocultos): postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
        
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar la conexión obteniendo información del servidor
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Versión de PostgreSQL: {db_version[0]}")
        
        # Listar las tablas existentes
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
        """)
        
        tables = cursor.fetchall()
        print("\nTablas existentes en la base de datos:")
        for table in tables:
            print(f" - {table[0]}")
        
        cursor.close()
        conn.close()
        print("\nConexión exitosa a la base de datos PostgreSQL")
        
    except Exception as e:
        print(f"ERROR: No se pudo conectar a la base de datos: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection() 