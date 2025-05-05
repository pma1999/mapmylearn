import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
import bcrypt # Import bcrypt globally as it might be needed

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
        
        # ------------------------------------------------------------------------
        # Crear usuario administrador inicial si no existe NINGUNO
        # ------------------------------------------------------------------------
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM users
            WHERE is_admin = TRUE
        );
        """)

        if not cursor.fetchone()[0]:
            print("\nAttempting to create initial admin user as none exist...")
            initial_admin_email = os.environ.get("INITIAL_ADMIN_EMAIL")
            initial_admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD")

            if not initial_admin_email or not initial_admin_password:
                print("\nERROR: INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD environment variables are required")
                print("       to create the initial admin user, but one or both are missing.")
                print("       Please set these variables securely and rerun the script.")
                print("       Skipping initial admin creation.")
                # Decide whether to exit or continue without admin creation.
                # For setup scripts, it might be better to exit if admin setup fails when expected.
                # Let's exit to make the failure explicit.
                conn.rollback() # Rollback any potential transaction state change
                cursor.close()
                conn.close()
                sys.exit("Exiting due to missing initial admin credentials.")
            else:
                print(f"Found INITIAL_ADMIN_EMAIL: {initial_admin_email}")
                print("WARNING: INITIAL_ADMIN_PASSWORD found (value not shown).")
                print("WARNING: These environment variables are sensitive and should only be")
                print("         used for the very first setup. Ensure they are stored securely")
                print("         (e.g., in a .env file NOT committed to git, or system environment).")

                # Hash the password securely at runtime
                hashed_password = bcrypt.hashpw(initial_admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                current_time = datetime.now()

                print(f"Creating initial admin user: {initial_admin_email}...")
                try:
                    cursor.execute("""
                    INSERT INTO users (email, hashed_password, full_name, is_active, is_admin, created_at, credits)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (initial_admin_email, hashed_password, 'Initial Admin', True, True, current_time, 1000)) # Default credits for initial admin
                    print("Initial admin user created successfully.")
                    print("RECOMMENDATION: Log in as this user and change the password immediately.")
                except psycopg2.Error as db_err:
                    print(f"\nERROR: Failed to insert initial admin user: {db_err}")
                    print("       Please check database logs and ensure the environment variables are correct.")
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    sys.exit("Exiting due to initial admin creation failure.")
        else:
            print("\nAn admin user already exists. Skipping initial admin creation.")

        # Commit changes if admin was created successfully or no admin creation was needed
        conn.commit()
        cursor.close()
        conn.close()
        print("\nEstructura de la base de datos aplicada con éxito")

    except psycopg2.Error as db_err:
        print(f"\nDATABASE ERROR during structure application: {str(db_err)}")
        # Attempt to close connection if it exists and is open
        if 'conn' in locals() and conn and not conn.closed:
            conn.rollback() # Rollback any partial transaction
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
        sys.exit(1)
    except Exception as e:
        print(f"\nGENERAL ERROR during structure application: {str(e)}")
        # Attempt to close connection if it exists and is open
        if 'conn' in locals() and conn and not conn.closed:
            conn.rollback() # Rollback any partial transaction
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
        sys.exit(1)

if __name__ == "__main__":
    apply_database_structure() 