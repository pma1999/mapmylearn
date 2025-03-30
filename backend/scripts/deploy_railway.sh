#!/bin/bash
# Script de despliegue para Railway
# Uso: ./scripts/deploy_railway.sh

set -e  # Salir inmediatamente si un comando falla

echo "=== Iniciando despliegue en Railway ==="

# Verificar que estamos en la rama correcta (main o master)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo "⚠️ ADVERTENCIA: No estás en la rama principal (main/master), estás en $CURRENT_BRANCH"
    read -p "¿Deseas continuar con el despliegue? (s/N): " CONFIRM
    if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
        echo "Despliegue cancelado."
        exit 1
    fi
fi

# Verificar instalación de Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ ERROR: Railway CLI no está instalado. Instálalo con 'npm i -g @railway/cli'"
    exit 1
fi

# Verificar login en Railway
echo "Verificando sesión en Railway..."
if ! railway whoami &> /dev/null; then
    echo "No has iniciado sesión en Railway. Iniciando sesión..."
    railway login
fi

# Generar clave JWT segura si no existe
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "Generando nueva clave JWT secreta..."
    export JWT_SECRET_KEY=$(openssl rand -hex 32)
    echo "Se ha generado una nueva clave JWT. Asegúrate de guardarla en un lugar seguro."
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
fi

# Confirmar variables de entorno
echo "===== Variables de entorno críticas ====="
echo "DATABASE_URL: ${DATABASE_URL:-(no establecida, se usará la de Railway)}"
echo "JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:8}***** (parcialmente oculta)"
echo "ENVIRONMENT: ${ENVIRONMENT:-production}"

# Verificar base de datos
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️ ADVERTENCIA: DATABASE_URL no está establecida localmente."
    echo "Se utilizará la variable de entorno configurada en Railway."
    echo "Asegúrate de que haya una base de datos PostgreSQL configurada en tu proyecto de Railway."
fi

# Ejecutar pruebas antes del despliegue
echo "===== Ejecutando pruebas previas al despliegue ====="
# Descomenta si tienes pruebas configuradas
# python -m pytest tests/

# Desplegar en Railway
echo "===== Desplegando en Railway ====="
railway up --detach

# Configurar variables de entorno en Railway si es necesario
if [ -n "$JWT_SECRET_KEY" ] && [ -n "$DATABASE_URL" ]; then
    echo "===== Configurando variables de entorno en Railway ====="
    railway variables set \
        JWT_SECRET_KEY="$JWT_SECRET_KEY" \
        DATABASE_URL="$DATABASE_URL" \
        ENVIRONMENT="production" \
        ENABLE_RATE_LIMITING="true"
fi

echo "===== Despliegue completado ====="
echo "Para ver los logs: railway logs"
echo "Para abrir la URL del proyecto: railway open" 