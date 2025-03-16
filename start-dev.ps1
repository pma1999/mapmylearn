#!/usr/bin/env pwsh
# Script para iniciar el Learning Path Generator en modo desarrollo

# Colores para mensajes
$ESC = [char]27
$Green = "$ESC[32m"
$Yellow = "$ESC[33m"
$Cyan = "$ESC[36m"
$Reset = "$ESC[0m"

Write-Host "${Cyan}Iniciando Learning Path Generator en modo desarrollo...${Reset}" -ForegroundColor Cyan

# Verifica si Node.js está instalado
try {
    $nodeVersion = node -v
    Write-Host "${Green}✓ Node.js detectado:${Reset} $nodeVersion" -ForegroundColor Green
} 
catch {
    Write-Host "${Yellow}⚠ Node.js no detectado. Por favor, instala Node.js desde https://nodejs.org/${Reset}" -ForegroundColor Yellow
    exit 1
}

# Verifica si Python está instalado
try {
    $pythonVersion = python --version
    Write-Host "${Green}✓ Python detectado:${Reset} $pythonVersion" -ForegroundColor Green
    $pythonCmd = "python"
} 
catch {
    try {
        $pythonVersion = python3 --version
        Write-Host "${Green}✓ Python detectado:${Reset} $pythonVersion" -ForegroundColor Green
        $pythonCmd = "python3"
    } 
    catch {
        Write-Host "${Yellow}⚠ Python no detectado. Por favor, instala Python 3.8+ desde https://python.org/${Reset}" -ForegroundColor Yellow
        exit 1
    }
}

# Instala dependencias del frontend si es necesario
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "${Yellow}Instalando dependencias del frontend...${Reset}" -ForegroundColor Yellow
    Set-Location -Path frontend
    npm install
    Set-Location -Path ..
} 
else {
    Write-Host "${Green}✓ Dependencias del frontend ya instaladas${Reset}" -ForegroundColor Green
}

# Verifica el entorno virtual de Python y lo crea si no existe
if (-not (Test-Path "venv")) {
    Write-Host "${Yellow}Creando entorno virtual de Python...${Reset}" -ForegroundColor Yellow
    & $pythonCmd -m venv venv
    
    # Activa el entorno virtual e instala dependencias
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell Core (6+)
        & ./venv/bin/Activate.ps1
    } 
    else {
        # Windows PowerShell
        & ./venv/Scripts/Activate.ps1
    }
    
    # Instala las dependencias del backend
    Write-Host "${Yellow}Instalando dependencias del backend...${Reset}" -ForegroundColor Yellow
    pip install -r requirements.txt
    pip install -r frontend/api/requirements.txt
} 
else {
    Write-Host "${Green}✓ Entorno virtual ya configurado${Reset}" -ForegroundColor Green
    # Activa el entorno virtual
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell Core (6+)
        & ./venv/bin/Activate.ps1
    } 
    else {
        # Windows PowerShell
        & ./venv/Scripts/Activate.ps1
    }
}

# Inicia el backend y el frontend en paralelo
try {
    Write-Host "${Cyan}Iniciando el backend en http://localhost:8000${Reset}" -ForegroundColor Cyan
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            # PowerShell Core (6+)
            & ./venv/bin/Activate.ps1
        } 
        else {
            # Windows PowerShell
            & ./venv/Scripts/Activate.ps1
        }
        cd frontend/api
        uvicorn app:app --reload --host 0.0.0.0 --port 8000
    }
    
    # Espera un momento para que el backend se inicie
    Start-Sleep -Seconds 2
    
    Write-Host "${Cyan}Iniciando el frontend en http://localhost:3000${Reset}" -ForegroundColor Cyan
    Set-Location -Path frontend
    npm start
} 
finally {
    # Limpiar jobs cuando se interrumpe
    if ($backendJob) {
        Stop-Job -Job $backendJob
        Remove-Job -Job $backendJob -Force
    }
    
    # Vuelve al directorio original
    Set-Location -Path $PSScriptRoot
    
    Write-Host "${Yellow}Aplicación detenida.${Reset}" -ForegroundColor Yellow
} 