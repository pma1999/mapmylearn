import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def make_admin(email="pablomiguelargudo@gmail.com"):
    """Otorga permisos de administrador a un usuario específico"""
    print(f"Configurando permisos de administrador para el usuario: {email}")
    
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
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id, email, is_admin FROM users WHERE email = %s;", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"ERROR: No se encontró ningún usuario con el email {email}")
            sys.exit(1)
        
        user_id, user_email, is_admin = user
        
        if is_admin:
            print(f"El usuario {email} ya tiene permisos de administrador.")
        else:
            # Actualizar permisos a administrador
            cursor.execute("UPDATE users SET is_admin = TRUE WHERE id = %s;", (user_id,))
            print(f"¡Permisos de administrador otorgados al usuario {email}!")
            
            # Asegurar que el usuario tiene créditos suficientes
            cursor.execute("UPDATE users SET credits = 1000 WHERE id = %s AND credits < 1000;", (user_id,))
            print(f"Créditos actualizados para el usuario {email}")
            
            # Registrar la transacción
            cursor.execute("""
            INSERT INTO credit_transactions (user_id, admin_user_id, amount, transaction_type, created_at, notes)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s);
            """, (
                user_id,
                user_id,  # El mismo usuario como admin para esta transacción
                1000,
                "admin_promotion",
                "Créditos otorgados por promoción a administrador"
            ))
            print(f"Transacción de créditos registrada para el usuario {email}")
        
        # Verificar el estado actual del usuario
        cursor.execute("SELECT id, email, full_name, is_admin, credits FROM users WHERE id = %s;", (user_id,))
        updated_user = cursor.fetchone()
        print(f"\nEstado actual del usuario:")
        print(f" - ID: {updated_user[0]}")
        print(f" - Email: {updated_user[1]}")
        print(f" - Nombre: {updated_user[2]}")
        print(f" - Admin: {updated_user[3]}")
        print(f" - Créditos: {updated_user[4]}")
        
        # Cerrar la conexión
        cursor.close()
        conn.close()
        
        print("\nOperación completada con éxito")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    make_admin() 