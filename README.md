# Learning Path Generator 🎓

Generador de Rutas de Aprendizaje impulsado por IA. Una aplicación que crea planes estructurados de aprendizaje para cualquier tema usando OpenAI y Tavily.

## Características ✨

- Generación de rutas de aprendizaje personalizadas para cualquier tema
- Procesamiento en paralelo para mayor velocidad
- Búsqueda web en tiempo real para obtener recursos actualizados
- Historial de rutas generadas con opciones de favoritos y etiquetas
- Interfaz moderna y responsive con soporte para modo oscuro
- API RESTful con documentación interactiva

## Requisitos 📋

- Python 3.8 o superior
- Node.js 14 o superior
- Claves API:
  - OpenAI API Key (para generación de texto)
  - Tavily API Key (para búsqueda web)

## Instalación 🔧

1. Clona este repositorio:
   ```
   git clone https://github.com/tuusuario/learning-path-generator.git
   cd learning-path-generator
   ```

2. Ejecuta el script de inicio en desarrollo:
   
   **Windows (PowerShell o CMD)**:
   ```
   .\start-dev.bat
   ```
   o
   ```
   powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
   ```

   **Linux/macOS**:
   ```
   chmod +x start-dev.sh
   ./start-dev.sh
   ```
   
   Este script automáticamente:
   - Crea un entorno virtual de Python
   - Instala todas las dependencias necesarias
   - Inicia el backend en http://localhost:8000
   - Inicia el frontend en http://localhost:3000

3. Abre un navegador y ve a http://localhost:3000

## Configuración ⚙️

En la primera ejecución, necesitarás configurar las claves API:

1. Ve a la página de Configuración desde el menú de navegación
2. Introduce tus claves API:
   - OpenAI API Key (obténla en https://platform.openai.com/api-keys)
   - Tavily API Key (obténla en https://tavily.com/)
3. Guarda los cambios

## Estructura del Proyecto 🏗️

```
learning-path-generator/
├── frontend/                # Frontend de React
│   ├── api/                 # API de FastAPI para servir al frontend
│   │   ├── api/                 # API de FastAPI para servir al frontend
│   │   ├── src/                 # Código fuente de React
│   │   │   ├── components/      # Componentes reutilizables
│   │   │   ├── contexts/        # Contextos de React (gestión de estado)
│   │   │   ├── pages/           # Páginas de la aplicación
│   │   │   ├── services/        # Servicios para comunicación con API
│   │   │   └── utils/           # Utilidades
│   │   ├── public/              # Archivos estáticos
│   │   └── package.json         # Dependencias de NPM
│   ├── history/                 # Servicio para gestionar el historial
│   ├── models/                  # Modelos y estructuras de datos
│   ├── prompts/                 # Plantillas para LLM
│   ├── start-dev.ps1            # Script para desarrollo (PowerShell)
│   ├── start-dev.sh             # Script para desarrollo (Bash)
│   └── start-dev.bat            # Script para desarrollo (Windows Batch)
```

## Modo de Uso 📝

1. **Generación de Rutas de Aprendizaje**:
   - Introduce un tema en la página principal
   - Ajusta las opciones de generación si lo deseas
   - Haz clic en "Generar Ruta de Aprendizaje"

2. **Gestión del Historial**:
   - Visualiza todas tus rutas de aprendizaje generadas
   - Marca favoritos, añade etiquetas, busca y filtra
   - Descarga rutas como archivos JSON

3. **Configuración**:
   - Gestiona tus claves API
   - Cambia entre modo claro y oscuro
   - Ajusta los valores predeterminados de generación

## Desarrollo 🧑‍💻

Para ejecutar la aplicación en modo desarrollo:

```bash
# Inicia el backend y frontend juntos
./start-dev.sh  # o .\start-dev.ps1 en Windows

# Para iniciar solo el backend
cd frontend/api
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Para iniciar solo el frontend
cd frontend
npm start
```

## Licencia 📄

Este proyecto está licenciado bajo [MIT License](LICENSE)

---

Hecho con ❤️ y OpenAI 