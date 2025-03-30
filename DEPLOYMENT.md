# Guía de Despliegue: Learni

Esta guía proporciona instrucciones detalladas sobre cómo desplegar la aplicación Learni en producción, utilizando Vercel para el frontend y Railway para el backend.

## Requisitos Previos

- Cuenta en [Railway](https://railway.app/)
- Cuenta en [Vercel](https://vercel.com/)
- Git instalado
- Node.js (v16 o superior)
- Python (v3.9 o superior)
- CLIs de Railway y Vercel (opcionales, pero recomendados)

## Estructura del Proyecto

Learni consiste en dos componentes principales:

1. **Frontend**: Aplicación React alojada en `./frontend/`
2. **Backend**: API FastAPI alojada en `./backend/`

## 1. Configuración de Variables de Entorno

### Backend (Railway)

Crea un archivo `.env` en el directorio `backend/` con las siguientes variables:

```
# PostgreSQL Database Configuration
DATABASE_URL=postgres://username:password@hostname:port/database_name

# JWT Authentication Settings
JWT_SECRET_KEY=your_secure_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment settings
ENVIRONMENT=production

# CORS settings
FRONTEND_URL=https://learny-peach.vercel.app

# Security settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=learning_path.log
DATA_LOGGING=true
JSON_FORMAT=true
```

### Frontend (Vercel)

Crea un archivo `.env.production` en el directorio `frontend/` con:

```
# API URL pointing to the Railway backend
REACT_APP_API_URL=https://your-railway-app-url.up.railway.app

# Additional settings
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENVIRONMENT=production
```

## 2. Despliegue del Backend en Railway

### Método Manual

1. Inicia sesión en Railway
   ```bash
   railway login
   ```

2. Inicializa el proyecto (si no está ya inicializado)
   ```bash
   cd backend
   railway init
   ```

3. Crea una base de datos PostgreSQL en Railway
   ```bash
   railway add plugin postgresql
   ```

4. Obtén la URL de la base de datos
   ```bash
   railway variables get DATABASE_URL
   ```

5. Configura las variables de entorno
   ```bash
   railway variables set JWT_SECRET_KEY=your_secure_secret_key
   railway variables set ENVIRONMENT=production
   railway variables set ENABLE_RATE_LIMITING=true
   railway variables set FRONTEND_URL=https://learni-peach.vercel.app
   ```

6. Despliega el proyecto
   ```bash
   railway up
   ```

### Método Automatizado

1. Ejecuta el script de despliegue
   ```bash
   chmod +x backend/scripts/deploy_railway.sh
   ./backend/scripts/deploy_railway.sh
   ```

2. Sigue las instrucciones en la terminal

### Post-despliegue

1. Ejecuta las migraciones de base de datos
   ```bash
   railway run python scripts/init_db.py
   ```

2. (Opcional) Crea un usuario administrador
   ```bash
   railway run python scripts/init_db.py --admin-email admin@example.com --admin-password securepassword
   ```

## 3. Despliegue del Frontend en Vercel

### Método Manual

1. Inicia sesión en Vercel
   ```bash
   vercel login
   ```

2. Navega al directorio del frontend
   ```bash
   cd frontend
   ```

3. Despliega en Vercel
   ```bash
   vercel
   ```

4. Configura las variables de entorno en la interfaz web de Vercel o mediante CLI
   ```bash
   vercel env add REACT_APP_API_URL production https://your-railway-app-url.up.railway.app
   vercel env add REACT_APP_ENVIRONMENT production production
   ```

5. Realiza el despliegue de producción
   ```bash
   vercel --prod
   ```

### Método Automatizado

1. Ejecuta el script de despliegue
   ```bash
   chmod +x frontend/scripts/deploy_vercel.sh
   ./frontend/scripts/deploy_vercel.sh
   ```

2. Sigue las instrucciones en la terminal

## 4. Configuración de Dominio Personalizado (Opcional)

### En Vercel
1. Ve a Dashboard > Learni > Settings > Domains
2. Agrega tu dominio personalizado (ej. learni.yourdomain.com)
3. Sigue las instrucciones para configurar los registros DNS

### En Railway
1. Ve a tu proyecto > Settings > Domains
2. Agrega tu dominio personalizado para la API (ej. api.learni.yourdomain.com)
3. Configura los registros DNS según las instrucciones

## 5. Monitorización y Mantenimiento

### Registros (Logs)
- **Backend**: Accede a los registros desde Railway dashboard o mediante CLI:
  ```bash
  railway logs
  ```

- **Frontend**: Accede a los registros desde Vercel dashboard o mediante CLI:
  ```bash
  vercel logs
  ```

### Copias de Seguridad de Base de Datos
1. Realiza una copia de seguridad periódica de la base de datos PostgreSQL
   ```bash
   railway run pg_dump -U postgres > backup_$(date +%Y%m%d).sql
   ```

2. Guarda las copias de seguridad en un lugar seguro

### Actualizaciones de Aplicación
1. Actualiza tu código en la rama principal (main/master)
2. Utiliza los scripts de despliegue o comandos manuales para actualizar las aplicaciones

## 6. Solución de Problemas Comunes

### El Backend No Se Conecta a la Base de Datos
- Verifica la variable `DATABASE_URL` en Railway
- Asegúrate de que la base de datos PostgreSQL esté activa

### CORS Error en el Frontend
- Verifica que la URL del frontend esté correctamente configurada en la variable `FRONTEND_URL` del backend
- Comprueba que la URL de la API en el frontend sea correcta

### Problemas de Autenticación
- Verifica que `JWT_SECRET_KEY` esté configurado en Railway
- Comprueba que las cookies funcionen correctamente (especialmente en dominios personalizados)

### Migraciones de Base de Datos
Si encuentras errores al ejecutar migraciones:
```bash
railway run python scripts/init_db.py --no-migrations
```

## Actualizaciones Futuras
Para actualizar tu aplicación desplegada:

1. Realiza cambios en tu código local
2. Ejecuta pruebas para asegurar que todo funciona correctamente
3. Haz commit y push a la rama principal
4. Ejecuta los scripts de despliegue para Railway y Vercel

¡Felicitaciones! Tu aplicación Learni debería estar correctamente desplegada y funcionando. 