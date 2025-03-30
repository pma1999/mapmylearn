#!/bin/bash
# Script para ejecutar la aplicación en modo desarrollo
# Uso: ./run_dev.sh

set -e  # Salir inmediatamente si un comando falla

# Función para verificar si un puerto está en uso
is_port_in_use() {
    if command -v nc &> /dev/null; then
        nc -z localhost $1 &> /dev/null
        return $?
    elif command -v lsof &> /dev/null; then
        lsof -i:$1 &> /dev/null
        return $?
    else
        # Fallback para Windows
        return 1  # Asumir que el puerto está libre
    fi
}

# Crear un archivo .env si no existe
if [ ! -f "backend/.env" ]; then
    echo "Creando archivo .env para desarrollo..."
    cat > backend/.env << EOL
# Database Configuration (SQLite para desarrollo)
DATABASE_URL=sqlite:///./learni_dev.db

# JWT Authentication Settings
JWT_SECRET_KEY=dev_secret_key_do_not_use_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment settings
ENVIRONMENT=development

# Security settings
ENABLE_RATE_LIMITING=false

# Logging configuration
LOG_LEVEL=DEBUG
LOG_FILE=learning_path.log
DATA_LOGGING=true
JSON_FORMAT=false
EOL
    echo ".env creado en backend/"
fi

# Verificar si Python y pip están instalados
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python no está instalado. Por favor, instala Python 3.9 o superior."
    exit 1
fi

# Usar python3 si está disponible, sino python
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Verificar si el entorno virtual existe, si no crearlo
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    $PYTHON -m venv venv
    echo "Entorno virtual creado en ./venv/"
fi

# Activar el entorno virtual
if [ -d "venv/Scripts" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS
    source venv/bin/activate
fi

# Instalar dependencias backend
echo "Instalando dependencias del backend..."
pip install -r backend/requirements.txt

# Inicializar la base de datos
echo "Inicializando la base de datos..."
cd backend
python scripts/init_db.py --no-migrations
cd ..

# Verificar si Node.js y npm están instalados
if ! command -v node &> /dev/null; then
    echo "⚠️ ADVERTENCIA: Node.js no está instalado. No se podrá ejecutar el frontend."
    read -p "¿Deseas continuar solo con el backend? (s/N): " CONTINUE_BACKEND
    if [ "$CONTINUE_BACKEND" != "s" ] && [ "$CONTINUE_BACKEND" != "S" ]; then
        echo "Instalación cancelada."
        exit 1
    fi
    # Ejecutar solo el backend
    echo "Iniciando el backend en http://localhost:8000..."
    cd backend
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
    exit 0
fi

# Instalar dependencias frontend
echo "Instalando dependencias del frontend..."
cd frontend
npm install
cd ..

# Ejecutar backend y frontend en paralelo
echo "Iniciando la aplicación en modo desarrollo..."

# Verificar puertos disponibles
BACKEND_PORT=8000
FRONTEND_PORT=3000

if is_port_in_use $BACKEND_PORT; then
    echo "❌ ERROR: El puerto $BACKEND_PORT ya está en uso. Por favor, cierra cualquier aplicación que esté usando este puerto."
    exit 1
fi

if is_port_in_use $FRONTEND_PORT; then
    echo "❌ ERROR: El puerto $FRONTEND_PORT ya está en uso. Por favor, cierra cualquier aplicación que esté usando este puerto."
    exit 1
fi

# Ejecutar backend y frontend en terminales separadas
if [ "$(uname)" == "Darwin" ] || [ "$(uname)" == "Linux" ]; then
    # Unix/Linux/MacOS
    echo "Iniciando backend en http://localhost:8000..."
    cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    echo "Iniciando frontend en http://localhost:3000..."
    cd frontend && npm start &
    FRONTEND_PID=$!
    
    # Manejar señales para terminar ambos procesos
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
    
    # Esperar a que cualquiera de los procesos termine
    wait
else
    # Windows - abrir en ventanas separadas
    echo "Iniciando backend y frontend en ventanas separadas..."
    start cmd /c "cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8000"
    start cmd /c "cd frontend && npm start"
    
    echo "Aplicación iniciada. Presiona Ctrl+C para detener este script."
    echo "Nota: En Windows, deberás cerrar manualmente las ventanas de los procesos cuando termines."
    # Mantener este script ejecutándose
    read -p "Presiona Enter para terminar este script..."
fi 