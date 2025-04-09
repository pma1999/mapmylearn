import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def list_users():
    """Lista todos los usuarios en la base de datos y sus créditos"""
    print("Obteniendo lista de usuarios y sus créditos...")
    
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
        
        # Consultar todos los usuarios
        cursor.execute("""
        SELECT id, email, full_name, is_admin, credits 
        FROM users 
        ORDER BY id;
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("No se encontraron usuarios en la base de datos.")
        else:
            print("\nUsuarios registrados en el sistema:")
            print("-" * 80)
            print(f"{'ID':<5} {'Email':<40} {'Nombre':<20} {'Admin':<6} {'Créditos':<10}")
            print("-" * 80)
            
            for user in users:
                user_id, email, full_name, is_admin, credits = user
                if full_name is None:
                    full_name = ""
                print(f"{user_id:<5} {email:<40} {full_name:<20} {str(is_admin):<6} {credits:<10}")
        
        # Obtener estadísticas
        cursor.execute("SELECT COUNT(*), SUM(credits), AVG(credits) FROM users;")
        stats = cursor.fetchone()
        
        print("\nEstadísticas:")
        print(f"Total de usuarios: {stats[0]}")
        print(f"Total de créditos: {stats[1]}")
        print(f"Promedio de créditos por usuario: {stats[2]:.2f}")
        
        # Obtener usuarios con rol de administrador
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE;")
        admin_count = cursor.fetchone()[0]
        print(f"Usuarios con rol de administrador: {admin_count}")
        
        # Cerrar la conexión
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_users() 