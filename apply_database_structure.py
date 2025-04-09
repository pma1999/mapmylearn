import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

def apply_database_structure():
    """Aplica la estructura completa de la base de datos según los modelos del proyecto"""
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
        
        # -------------------------------------------------------------------------
        # Verificar y crear tablas que faltan
        # -------------------------------------------------------------------------
        
        # 1. Verificar tabla users
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'users'
        );
        """)
        
        if not cursor.fetchone()[0]:
            print("Creando tabla 'users'...")
            cursor.execute("""
            CREATE TABLE users (
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
            CREATE INDEX idx_user_email ON users (email);
            """)
            print("Tabla 'users' creada correctamente")
        else:
            # Verificar y añadir columnas que faltan en users
            columns_to_check = [
                ("is_admin", "BOOLEAN DEFAULT FALSE"),
                ("credits", "INTEGER DEFAULT 0 NOT NULL")
            ]
            
            for column_name, column_def in columns_to_check:
                cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = '{column_name}'
                );
                """)
                
                if not cursor.fetchone()[0]:
                    print(f"Añadiendo columna '{column_name}' a la tabla 'users'...")
                    cursor.execute(f"""
                    ALTER TABLE users ADD COLUMN {column_name} {column_def};
                    """)
                    print(f"Columna '{column_name}' añadida correctamente")
        
        # 2. Verificar tabla credit_transactions
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'credit_transactions'
        );
        """)
        
        if not cursor.fetchone()[0]:
            print("Creando tabla 'credit_transactions'...")
            cursor.execute("""
            CREATE TABLE credit_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                admin_user_id INTEGER,
                amount INTEGER NOT NULL,
                transaction_type VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                notes VARCHAR,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            CREATE INDEX idx_credit_transaction_user_id ON credit_transactions (user_id);
            CREATE INDEX idx_credit_transaction_admin_id ON credit_transactions (admin_user_id);
            CREATE INDEX idx_credit_transaction_created_at ON credit_transactions (created_at DESC);
            CREATE INDEX idx_credit_transaction_action_type ON credit_transactions (transaction_type);
            """)
            print("Tabla 'credit_transactions' creada correctamente")
        
        # 3. Verificar tabla sessions
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'sessions'
        );
        """)
        
        if not cursor.fetchone()[0]:
            print("Creando tabla 'sessions'...")
            cursor.execute("""
            CREATE TABLE sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                refresh_token VARCHAR UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                device_info VARCHAR,
                ip_address VARCHAR,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX idx_session_token ON sessions (refresh_token);
            """)
            print("Tabla 'sessions' creada correctamente")
        
        # 4. Verificar tabla learning_paths
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'learning_paths'
        );
        """)
        
        if not cursor.fetchone()[0]:
            print("Creando tabla 'learning_paths'...")
            cursor.execute("""
            CREATE TABLE learning_paths (
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
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX idx_learning_path_user_id ON learning_paths (user_id);
            CREATE INDEX idx_learning_path_path_id ON learning_paths (path_id);
            CREATE INDEX idx_learning_path_topic ON learning_paths (topic);
            CREATE INDEX idx_learning_path_user_date ON learning_paths (user_id, creation_date DESC);
            CREATE INDEX idx_learning_path_user_favorite ON learning_paths (user_id, favorite);
            CREATE INDEX idx_learning_path_user_modified ON learning_paths (user_id, last_modified_date DESC);
            CREATE INDEX idx_learning_path_user_source ON learning_paths (user_id, source);
            CREATE INDEX idx_learning_path_user_fav_date ON learning_paths (user_id, favorite, creation_date DESC);
            """)
            print("Tabla 'learning_paths' creada correctamente")
        
        # 5. Verificar tabla alembic_version
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        );
        """)
        
        if not cursor.fetchone()[0]:
            print("Creando tabla 'alembic_version'...")
            cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL,
                PRIMARY KEY (version_num)
            );
            INSERT INTO alembic_version (version_num) VALUES ('3877029518ce');
            """)
            print("Tabla 'alembic_version' creada correctamente")
        else:
            # Actualizar la versión de alembic
            print("Actualizando versión de alembic...")
            cursor.execute("""
            UPDATE alembic_version SET version_num = '3877029518ce';
            """)
            print("Versión de alembic actualizada correctamente")
        
        # Crear usuario admin si no existe
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM users 
            WHERE email = 'admin@learny.app'
        );
        """)
        
        if not cursor.fetchone()[0]:
            # Contraseña hasheada para 'admin123' (solo para fines de demostración)
            import bcrypt
            password = 'admin123'
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            current_time = datetime.now()
            
            print("Creando usuario admin...")
            cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_admin, created_at, credits)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, ('admin@learny.app', hashed_password, 'Admin User', True, True, current_time, 1000))
            print("Usuario admin creado correctamente")
        
        cursor.close()
        conn.close()
        print("\nEstructura de la base de datos aplicada con éxito")
        
    except Exception as e:
        print(f"ERROR durante la aplicación de la estructura: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    apply_database_structure() 