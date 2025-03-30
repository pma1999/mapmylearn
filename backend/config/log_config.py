import logging
import os
import json
from datetime import datetime
import sys
import traceback
from logging.handlers import RotatingFileHandler

TRACE = 5  # Custom trace level

# Constantes para niveles de log
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def get_log_level(level_str):
    """
    Convierte un string de nivel de logging a la constante correspondiente.
    """
    return LOG_LEVELS.get(level_str.upper(), logging.INFO)

class JsonFormatter(logging.Formatter):
    """
    Formateador personalizado para logs en formato JSON.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Añadir excepción si existe
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Añadir atributos extra si existen
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename",
                          "funcName", "id", "levelname", "levelno", "lineno",
                          "module", "msecs", "message", "msg", "name", "pathname",
                          "process", "processName", "relativeCreated", "stack_info",
                          "thread", "threadName"]:
                log_record[key] = value
        
        return json.dumps(log_record)

def setup_logging(
    log_file=None,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    enable_json_logs=False,
    data_logging=True,
    max_bytes=10*1024*1024,  # 10 MB
    backup_count=5
):
    """
    Configura el sistema de logging para la aplicación.
    
    Args:
        log_file: Ruta al archivo de log. Si es None, solo se logea a consola.
        console_level: Nivel de log para la consola.
        file_level: Nivel de log para el archivo.
        enable_json_logs: Si es True, se formatean los logs como JSON.
        data_logging: Si es True, se permiten logs de datos detallados.
        max_bytes: Tamaño máximo del archivo de log antes de rotar.
        backup_count: Número de archivos de backup a mantener.
    """
    # Determinar entorno
    environment = os.getenv("ENVIRONMENT", "development")
    is_production = environment == "production"
    
    # Configuración base
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Permitir todos los niveles y filtrar en los handlers
    
    # Limpiar handlers existentes para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear consola handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    
    # Configurar formato basado en el entorno y preferencias
    if enable_json_logs or is_production:
        console_formatter = JsonFormatter()
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
        )
    
    console.setFormatter(console_formatter)
    root_logger.addHandler(console)
    
    # Configurar archivo de log si se proporciona ruta
    if log_file:
        try:
            # Usar RotatingFileHandler para limitar tamaño y permitir rotación
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(file_level)
            
            # Usar siempre JSON para archivos de log en producción
            if enable_json_logs or is_production:
                file_formatter = JsonFormatter()
            else:
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
                )
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            logging.info(f"Log file initialized at {log_file}")
        except Exception as e:
            logging.error(f"Could not set up file logging: {str(e)}")
    
    # Configurar bibliotecas externas para no ser tan verbosas
    if is_production:
        # Reducir ruido de bibliotecas en producción
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Variable global para controlar logging detallado de datos
    global DATA_LOGGING_ENABLED
    DATA_LOGGING_ENABLED = data_logging
    
    # Registrar inicio del sistema
    logging.info(f"Logging initialized. Environment: {environment}, JSON formatting: {enable_json_logs}, Data logging: {data_logging}")
    return root_logger


# Variable global para controlar si se debe loguear datos extensos
DATA_LOGGING_ENABLED = False

def log_debug_data(message, data, limit=1000):
    """
    Loguea datos de depuración, posiblemente truncándolos si son muy grandes.
    Solo si DATA_LOGGING_ENABLED es True.
    """
    if not DATA_LOGGING_ENABLED:
        return
    
    try:
        # Convertir a JSON si es un objeto
        if not isinstance(data, str):
            data_str = json.dumps(data)
        else:
            data_str = data
        
        # Truncar si es muy grande
        if len(data_str) > limit:
            truncated = data_str[:limit] + f"... [truncated, total length: {len(data_str)}]"
            logging.debug(f"{message}: {truncated}")
        else:
            logging.debug(f"{message}: {data_str}")
    except Exception as e:
        logging.debug(f"{message}: [Error serializing data: {str(e)}]")


def log_info_data(message, data=None):
    """
    Loguea un mensaje informativo con datos opcionales.
    No trunca y siempre se muestra independientemente de DATA_LOGGING_ENABLED.
    """
    if data is None:
        logging.info(message)
        return
    
    try:
        # Convertir a JSON si es un objeto
        if not isinstance(data, str):
            data_str = json.dumps(data)
        else:
            data_str = data
        
        logging.info(f"{message}: {data_str}")
    except Exception as e:
        logging.info(f"{message}: [Error serializing data: {str(e)}]")
