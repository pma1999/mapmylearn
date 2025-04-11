import os
import sys
import subprocess

def run_railway_command(sql_command):
    """Ejecuta un comando SQL en la base de datos PostgreSQL a través de railway run"""
    try:
        print(f"Ejecutando SQL: {sql_command}")
        # Crear un comando para railway que ejecute psql con el SQL, sin usar cat que no existe en Windows
        railway_cmd = f'railway run "psql -c \\"{sql_command}\\""'
        
        # Ejecutar el comando
        result = subprocess.run(railway_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Verificar si hubo errores
        if result.returncode != 0:
            print(f"Error al ejecutar el comando: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        print(f"Error general al ejecutar el comando: {str(e)}")
        return False, str(e)

def apply_database_structure():
    """Configura la estructura de la base de datos PostgreSQL en Railway"""
    print("Configurando la estructura de la base de datos en Railway...")
    
    # 1. Verificar las tablas existentes
    success, output = run_railway_command("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    if not success:
        print("Error al verificar las tablas existentes")
        sys.exit(1)
        
    print(f"Tablas existentes:\n{output}")
    
    # 2. Crear tabla users si no existe
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
    
    success, output = run_railway_command(create_users_table)
    if not success:
        print("Error al crear la tabla users")
    else:
        print("Tabla users verificada/creada correctamente")
    
    # 3. Crear tabla credit_transactions si no existe
    create_credit_transactions_table = """
    CREATE TABLE IF NOT EXISTS credit_transactions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        admin_user_id INTEGER,
        amount INTEGER NOT NULL,
        transaction_type VARCHAR NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        notes VARCHAR,
        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_admin FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    CREATE INDEX IF NOT EXISTS idx_credit_transaction_user_id ON credit_transactions (user_id);
    CREATE INDEX IF NOT EXISTS idx_credit_transaction_admin_id ON credit_transactions (admin_user_id);
    CREATE INDEX IF NOT EXISTS idx_credit_transaction_created_at ON credit_transactions (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_credit_transaction_action_type ON credit_transactions (transaction_type);
    """
    
    success, output = run_railway_command(create_credit_transactions_table)
    if not success:
        print("Error al crear la tabla credit_transactions")
    else:
        print("Tabla credit_transactions verificada/creada correctamente")
    
    # 4. Crear tabla sessions si no existe
    create_sessions_table = """
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        refresh_token VARCHAR UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        device_info VARCHAR,
        ip_address VARCHAR,
        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_session_token ON sessions (refresh_token);
    """
    
    success, output = run_railway_command(create_sessions_table)
    if not success:
        print("Error al crear la tabla sessions")
    else:
        print("Tabla sessions verificada/creada correctamente")
    
    # 5. Crear tabla learning_paths si no existe
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
        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
    
    success, output = run_railway_command(create_learning_paths_table)
    if not success:
        print("Error al crear la tabla learning_paths")
    else:
        print("Tabla learning_paths verificada/creada correctamente")
    
    # 6. Crear tabla alembic_version si no existe
    create_alembic_version_table = """
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL,
        PRIMARY KEY (version_num)
    );
    """
    
    success, output = run_railway_command(create_alembic_version_table)
    if not success:
        print("Error al crear la tabla alembic_version")
    else:
        print("Tabla alembic_version verificada/creada correctamente")
    
    # 7. Establecer la versión de alembic
    update_alembic_version = """
    INSERT INTO alembic_version (version_num) 
    VALUES ('3877029518ce')
    ON CONFLICT (version_num) DO UPDATE SET version_num = '3877029518ce';
    """
    
    success, output = run_railway_command(update_alembic_version)
    if not success:
        print("Error al actualizar la versión de alembic")
    else:
        print("Versión de alembic actualizada correctamente")
    
    # 8. Verificar si existe el usuario admin
    check_admin_user = """
    SELECT EXISTS (SELECT 1 FROM users WHERE email = 'admin@mapmylearn.app');
    """
    
    success, output = run_railway_command(check_admin_user)
    if not success:
        print("Error al verificar el usuario admin")
    else:
        # Si el usuario admin no existe, crearlo
        if "f" in output:  # PostgreSQL devuelve 't' para true y 'f' para false
            create_admin_user = """
            INSERT INTO users (email, hashed_password, full_name, is_active, is_admin, credits, created_at)
            VALUES ('admin@mapmylearn.app', '$2b$12$8VK5NL.wBV.LD9kx9Ulhme/R/M.QyD1m9F/FA8qSh5CH3kB3CzKJi', 'Admin User', true, true, 1000, CURRENT_TIMESTAMP);
            """
            
            success, output = run_railway_command(create_admin_user)
            if not success:
                print("Error al crear el usuario admin")
            else:
                print("Usuario admin creado correctamente")
        else:
            print("El usuario admin ya existe")
    
    print("\nEstructura de la base de datos aplicada con éxito")

if __name__ == "__main__":
    apply_database_structure() 