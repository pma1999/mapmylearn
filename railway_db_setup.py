import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

def setup_database():
    """
    Configura la estructura de la base de datos PostgreSQL.
    Este script está diseñado para ejecutarse dentro del contenedor de Railway.
    """
    print("Iniciando configuración de la base de datos...")
    
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
        WHERE table_schema = 'public';
        """)
        
        tables = cursor.fetchall()
        print("\nTablas existentes en la base de datos:")
        for table in tables:
            print(f" - {table[0]}")
        
        # 1. Crear tabla users si no existe
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR UNIQUE NOT NULL,
            hashed_password VARCHAR NOT NULL,
            full_name VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            last_login TIMESTAMP,
            credits INTEGER DEFAULT 0 NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_user_email ON users (email);
        """
        
        cursor.execute(create_users_table)
        print("Tabla users verificada/creada correctamente")
        
        # 2. Crear tabla credit_transactions si no existe
        create_credit_transactions_table = """
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            admin_user_id INTEGER,
            amount INTEGER NOT NULL,
            transaction_type VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            notes VARCHAR,
            CONSTRAINT fk_user_ct FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_admin_ct FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_credit_transaction_user_id ON credit_transactions (user_id);
        CREATE INDEX IF NOT EXISTS idx_credit_transaction_admin_id ON credit_transactions (admin_user_id);
        CREATE INDEX IF NOT EXISTS idx_credit_transaction_created_at ON credit_transactions (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_credit_transaction_action_type ON credit_transactions (transaction_type);
        """
        
        cursor.execute(create_credit_transactions_table)
        print("Tabla credit_transactions verificada/creada correctamente")
        
        # 3. Crear tabla sessions si no existe
        create_sessions_table = """
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            refresh_token VARCHAR UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            device_info VARCHAR,
            ip_address VARCHAR,
            CONSTRAINT fk_user_sessions FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_session_token ON sessions (refresh_token);
        """
        
        cursor.execute(create_sessions_table)
        print("Tabla sessions verificada/creada correctamente")
        
        # 4. Crear tabla learning_paths si no existe
        create_learning_paths_table = """
        CREATE TABLE IF NOT EXISTS learning_paths (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            path_id VARCHAR NOT NULL,
            topic VARCHAR NOT NULL,
            path_data JSONB NOT NULL,
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            last_modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            favorite BOOLEAN DEFAULT FALSE,
            tags JSONB DEFAULT '[]',
            source VARCHAR DEFAULT 'generated',
            CONSTRAINT fk_user_lp FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_id ON learning_paths (user_id);
        CREATE INDEX IF NOT EXISTS idx_learning_path_path_id ON learning_paths (path_id);
        CREATE INDEX IF NOT EXISTS idx_learning_path_topic ON learning_paths (topic);
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_date ON learning_paths (user_id, creation_date DESC);
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_favorite ON learning_paths (user_id, favorite);
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_modified ON learning_paths (user_id, last_modified_date DESC);
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_source ON learning_paths (user_id, source);
        CREATE INDEX IF NOT EXISTS idx_learning_path_user_fav_date ON learning_paths (user_id, favorite, creation_date DESC);
        """
        
        cursor.execute(create_learning_paths_table)
        print("Tabla learning_paths verificada/creada correctamente")
        
        # 5. Crear tabla alembic_version si no existe
        create_alembic_version_table = """
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            PRIMARY KEY (version_num)
        );
        """
        
        cursor.execute(create_alembic_version_table)
        print("Tabla alembic_version verificada/creada correctamente")
        
        # 6. Establecer la versión de alembic
        cursor.execute("SELECT COUNT(*) FROM alembic_version;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('3877029518ce');")
            print("Versión de alembic insertada correctamente")
        else:
            cursor.execute("UPDATE alembic_version SET version_num = '3877029518ce';")
            print("Versión de alembic actualizada correctamente")
        
        # 7. Verificar si existe el usuario admin
        cursor.execute("SELECT EXISTS (SELECT 1 FROM users WHERE email = 'admin@learncompass.app');")
        admin_exists = cursor.fetchone()[0]
        
        if not admin_exists:
            # Crear un hash bcrypt para la contraseña 'admin123'
            # Nota: Esta contraseña es predefinida para simplificar el ejemplo
            hashed_password = '$2b$12$8VK5NL.wBV.LD9kx9Ulhme/R/M.QyD1m9F/FA8qSh5CH3kB3CzKJi'
            
            cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_admin, credits, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, ('admin@learncompass.app', hashed_password, 'Admin User', True, True, 1000, datetime.now()))
            print("Usuario admin creado correctamente")
        else:
            print("El usuario admin ya existe")
        
        # Cerrar la conexión
        cursor.close()
        conn.close()
        
        print("\nEstructura de la base de datos configurada con éxito")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database() 