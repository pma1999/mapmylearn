# Sistema de Historial de Rutas de Aprendizaje

Este módulo implementa un sistema completo para guardar, gestionar y recuperar rutas de aprendizaje generadas o importadas. El historial se almacena localmente en el navegador del usuario, garantizando privacidad y persistencia entre sesiones.

## Características principales

- **Almacenamiento local persistente**: Las rutas de aprendizaje se guardan en el almacenamiento local del navegador (utilizando `session_state` de Streamlit como interfaz)
- **Compresión de datos**: Los datos se comprimen automáticamente para optimizar el espacio en localStorage
- **Segmentación inteligente**: Si el historial crece demasiado, se segmenta en partes más pequeñas para evitar los límites de localStorage
- **Favoritos y etiquetas**: Posibilidad de marcar rutas como favoritas y añadir etiquetas personalizadas
- **Filtrado y búsqueda**: Filtro por tema, origen (generado/importado) y ordenación por diferentes criterios
- **Importación/Exportación**: Importar rutas individuales o exportar todo el historial para respaldo

## Cómo funciona

El sistema utiliza tres componentes principales:

1. **Modelos de datos** (`history_models.py`): Define las estructuras de datos para el historial
2. **Servicio de persistencia** (`history_service.py`): Maneja el almacenamiento, carga y operaciones sobre el historial
3. **Interfaz de usuario** (`history_ui.py`): Componentes visuales para interactuar con el historial

## Flujo de usuario

### Para guardar rutas generadas:
1. Genera una ruta de aprendizaje normalmente
2. La ruta se guarda automáticamente en el historial (si la opción está activada)
3. Alternativamente, usa el botón "Guardar en historial" para guardarla manualmente

### Para importar rutas existentes:
1. Usa el cargador de archivos en la pestaña "Generador" o en la pestaña "Historial"
2. Selecciona un archivo JSON con el formato correcto
3. Confirma la importación

### Para gestionar el historial:
1. Navega a la pestaña "Historial"
2. Explora las rutas guardadas, filtra y ordena según tus necesidades
3. Utiliza las opciones para:
   - Ver una ruta completa
   - Descargar una ruta específica
   - Añadir/eliminar etiquetas
   - Marcar/desmarcar como favorita
   - Eliminar rutas no deseadas

## Almacenamiento y límites

El sistema utiliza el localStorage del navegador a través de la API de `session_state` de Streamlit. Esto tiene algunas consideraciones:

- Los datos persisten entre recargas de página y sesiones del navegador
- El límite típico de localStorage es de 5-10 MB dependiendo del navegador
- El sistema comprime los datos y los segmenta si es necesario
- Todo se almacena localmente, no hay envío de datos a servidores externos

## Exportación para respaldo

Recomendamos exportar periódicamente el historial completo como respaldo:

1. Ve a la pestaña "Historial"
2. Usa el botón "Exportar todo el historial"
3. Guarda el archivo JSON resultante en un lugar seguro

## Implementación técnica

El sistema implementa varias optimizaciones:

- **Compresión zlib + base64**: Reduce significativamente el tamaño de los datos almacenados
- **Almacenamiento segmentado**: Divide automáticamente los datos grandes en segmentos manejables
- **Caching en memoria**: Evita operaciones repetidas de serialización/deserialización durante una sesión
- **Manejo de errores robusto**: Recuperación elegante ante datos corruptos o incompletos

## Privacidad

Todos los datos se almacenan exclusivamente en el dispositivo del usuario. No hay sincronización con servidores ni almacenamiento en la nube, garantizando máxima privacidad. 