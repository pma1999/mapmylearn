@echo off
echo Iniciando Learning Path Generator en modo desarrollo...
echo.

:: Ejecuta el script PowerShell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

:: Pausa al final para ver cualquier mensaje de error
pause 