@echo off
echo Iniciando el backend de Learning Path Generator...
echo.

:: Activa el entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Entorno virtual activado.
) else (
    echo No se encontró un entorno virtual. Se recomienda ejecutar start-dev.bat primero.
    exit /b 1
)

:: Inicia el backend
echo Iniciando el servidor FastAPI en http://localhost:8000
cd frontend/api
uvicorn app:app --reload --host 0.0.0.0 --port 8000

:: Si hay un error al ejecutar uvicorn
if %ERRORLEVEL% neq 0 (
    echo Error al iniciar el servidor. Verifica que todas las dependencias estén instaladas.
    exit /b 1
)

pause 