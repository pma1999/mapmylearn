#!/usr/bin/env python
"""
Script para inicializar la base de datos y configurar Alembic para migraciones.
Uso: python scripts/init_db.py
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Asegurar que podemos importar desde el directorio raíz
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import Base, engine
from models.auth_models import User, Session, LearningPath


def setup_db(use_migrations=True):
    """
    Configura la base de datos: crea tablas o ejecuta migraciones.
    
    Args:
        use_migrations: Si es True, configura y ejecuta migraciones de Alembic.
                       Si es False, crea tablas directamente con SQLAlchemy.
    """
    if use_migrations:
        print("Configurando Alembic para migraciones...")
        # Verificar si ya existe el directorio de migraciones
        migrations_dir = Path(__file__).parent.parent / "migrations"
        
        if not migrations_dir.exists():
            print("Iniciando Alembic...")
            subprocess.run(["alembic", "init", "migrations"], check=True)
            print("Directorio de migraciones creado.")
        
        # Generar migración inicial si no existe
        versions_dir = migrations_dir / "versions"
        if not versions_dir.exists() or not any(versions_dir.iterdir()):
            print("Generando migración inicial...")
            subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True)
            print("Migración inicial generada.")
        
        # Ejecutar migraciones
        print("Ejecutando migraciones...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migraciones aplicadas con éxito.")
    else:
        print("Creando tablas directamente con SQLAlchemy...")
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas con éxito.")


def create_admin_user(email, password):
    """
    Crea un usuario administrador si no existe.
    
    Args:
        email: Email del administrador
        password: Contraseña del administrador
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from sqlalchemy.orm import Session as SQLAlchemySession
    from utils.auth import get_password_hash
    
    # Verificar si ya existe el usuario
    with SQLAlchemySession(engine) as db:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"El usuario {email} ya existe, no se creará uno nuevo.")
            return
        
        # Crear usuario
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name="Administrator",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Usuario administrador {email} creado con éxito.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configurar la base de datos y crear usuarios iniciales")
    parser.add_argument("--no-migrations", action="store_true", help="No usar Alembic, crear tablas directamente")
    parser.add_argument("--admin-email", type=str, help="Email para usuario administrador inicial")
    parser.add_argument("--admin-password", type=str, help="Contraseña para usuario administrador inicial")
    
    args = parser.parse_args()
    
    # Configurar base de datos
    setup_db(not args.no_migrations)
    
    # Crear usuario administrador si se proporcionaron credenciales
    if args.admin_email and args.admin_password:
        create_admin_user(args.admin_email, args.admin_password) 