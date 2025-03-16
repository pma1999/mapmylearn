@echo off
echo Iniciando el frontend de Learning Path Generator...
echo.

:: Verifica si node_modules existe
if not exist frontend\node_modules (
    echo Instalando dependencias del frontend...
    cd frontend
    npm install
    cd ..
)

:: Inicia el frontend
echo Iniciando el frontend React en http://localhost:3000
echo IMPORTANTE: Asegúrate de que el backend esté en ejecución en http://localhost:8000
cd frontend
npm start

:: Si hay un error al ejecutar npm start
if %ERRORLEVEL% neq 0 (
    echo Error al iniciar el frontend. Verifica que todas las dependencias estén instaladas.
    exit /b 1
)

pause 