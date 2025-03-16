#!/bin/bash
# Script para iniciar el Learning Path Generator en modo desarrollo

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Iniciando Learning Path Generator en modo desarrollo...${NC}"

# Verifica si Node.js está instalado
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js detectado:${NC} $NODE_VERSION"
else
    echo -e "${YELLOW}⚠ Node.js no detectado. Por favor, instala Node.js desde https://nodejs.org/${NC}"
    exit 1
fi

# Verifica si Python está instalado
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python detectado:${NC} $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✓ Python detectado:${NC} $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo -e "${YELLOW}⚠ Python no detectado. Por favor, instala Python 3.8+ desde https://python.org/${NC}"
    exit 1
fi

# Instala dependencias del frontend si es necesario
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Instalando dependencias del frontend...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✓ Dependencias del frontend ya instaladas${NC}"
fi

# Verifica el entorno virtual de Python y lo crea si no existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual de Python...${NC}"
    $PYTHON_CMD -m venv venv
    
    # Activa el entorno virtual e instala dependencias
    source venv/bin/activate
    
    # Instala las dependencias del backend
    echo -e "${YELLOW}Instalando dependencias del backend...${NC}"
    pip install -r requirements.txt
    pip install -r frontend/api/requirements.txt
else
    echo -e "${GREEN}✓ Entorno virtual ya configurado${NC}"
    # Activa el entorno virtual
    source venv/bin/activate
fi

# Inicia el backend y el frontend en paralelo
echo -e "${CYAN}Iniciando el backend en http://localhost:8000${NC}"
(cd frontend/api && uvicorn app:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

# Espera un momento para que el backend se inicie
sleep 2

echo -e "${CYAN}Iniciando el frontend en http://localhost:3000${NC}"
cd frontend
npm start &
FRONTEND_PID=$!

# Maneja la interrupción para cerrar ambos procesos
trap cleanup INT TERM
cleanup() {
    echo -e "\n${YELLOW}Deteniendo la aplicación...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Espera a que alguno de los procesos termine
wait $BACKEND_PID $FRONTEND_PID
cleanup 