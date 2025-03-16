LEARNING PATH GENERATOR - INSTRUCCIONES DE EJECUCIÓN
===============================================

INICIO RÁPIDO EN WINDOWS:
------------------------
1. Haz doble clic en 'start-dev.bat'
2. Espera a que se instalen las dependencias y se inicie la aplicación
3. Abre tu navegador en http://localhost:3000

INICIO EN POWERSHELL (WINDOWS):
-----------------------------
1. Abre PowerShell (Windows + X, luego elige "Windows PowerShell" o "Terminal")
2. Navega hasta el directorio del proyecto:
   cd ruta\hacia\learning-path-generator
3. Ejecuta:
   .\start-dev.ps1

INICIO EN LINUX/MACOS:
--------------------
1. Abre una terminal
2. Navega hasta el directorio del proyecto:
   cd ruta/hacia/learning-path-generator
3. Haz ejecutable el script:
   chmod +x start-dev.sh
4. Ejecuta:
   ./start-dev.sh

REQUISITOS:
---------
- Python 3.8 o superior
- Node.js 14 o superior
- Claves API (configurables en la aplicación):
  - OpenAI API Key (https://platform.openai.com/api-keys)
  - Tavily API Key (https://tavily.com/)

NOTAS:
-----
- La primera vez que ejecutes la aplicación, se creará un entorno virtual y se instalarán todas las dependencias.
- El backend se ejecuta en http://localhost:8000
- El frontend se ejecuta en http://localhost:3000
- Configura tus claves API en la página de Configuración antes de usar la aplicación.

SOLUCIÓN DE PROBLEMAS:
--------------------
- Si encuentras errores de dependencias, intenta eliminar la carpeta 'venv' y ejecutar el script de inicio nuevamente.
- Si el puerto 3000 o 8000 está ocupado, modifica los scripts para usar puertos diferentes.
- Para más información, consulta el archivo README.md 