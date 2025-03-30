#!/bin/bash
# Script de despliegue para Vercel
# Uso: ./scripts/deploy_vercel.sh

set -e  # Salir inmediatamente si un comando falla

echo "=== Iniciando despliegue en Vercel ==="

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

# Verificar instalación de Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ ERROR: Vercel CLI no está instalado. Instálalo con 'npm i -g vercel'"
    exit 1
fi

# Verificar login en Vercel
echo "Verificando sesión en Vercel..."
if ! vercel whoami &> /dev/null; then
    echo "No has iniciado sesión en Vercel. Iniciando sesión..."
    vercel login
fi

# Verificar las variables de entorno
if [ -z "$REACT_APP_API_URL" ]; then
    echo "⚠️ ADVERTENCIA: REACT_APP_API_URL no está establecida."
    read -p "Introduce la URL del backend (ej: https://web-production-62f88.up.railway.app): " BACKEND_URL
    export REACT_APP_API_URL="$BACKEND_URL"
fi

# Mostrar información de despliegue
echo "===== Variables de entorno ====="
echo "REACT_APP_API_URL: $REACT_APP_API_URL"
echo "REACT_APP_ENVIRONMENT: production"

# Ejecutar pruebas antes del despliegue
echo "===== Realizando build previo para detectar errores ====="
npm run build

echo "===== Desplegando en Vercel ====="
vercel deploy --prod

# Configurar variables de entorno en Vercel si es necesario
echo "===== Configurando variables de entorno en Vercel ====="
vercel env add REACT_APP_API_URL production "$REACT_APP_API_URL"
vercel env add REACT_APP_ENVIRONMENT production "production"

echo "===== Despliegue completado ====="
echo "Para ver tu aplicación: vercel open" 