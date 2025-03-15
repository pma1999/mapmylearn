import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
import sys
import traceback

# Niveles de logging personalizados
TRACE = 5  # Nivel inferior a DEBUG para datos muy detallados

class JsonFormatter(logging.Formatter):
    """Formateador que convierte los registros de log en formato JSON estructurado."""
    def format(self, record):
        # Custom JSON encoder to handle non-serializable objects
        def custom_json_default(obj):
            if callable(obj):
                return f"<function: {getattr(obj, '__name__', 'anonymous')}>"
            return str(obj)
        
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar datos extra si existen
        if hasattr(record, 'data') and record.data:
            log_record["data"] = record.data
            
        # Agregar información de excepción si existe
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        try:
            return json.dumps(log_record, default=custom_json_default)
        except Exception as e:
            # Fallback if JSON serialization fails
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": f"[JSON serialization error: {str(e)}] {record.getMessage()}",
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            })

def setup_logging(
    log_file: Optional[str] = "learning_path.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_json_logs: bool = True,
    data_logging: bool = True
) -> None:
    """
    Configura el sistema de logging con opciones flexibles.
    
    Args:
        log_file: Ruta al archivo de log. None para deshabilitar logging a archivo.
        console_level: Nivel de logging para salida de consola.
        file_level: Nivel de logging para el archivo.
        enable_json_logs: Si es True, usa formato JSON para logs estructurados.
        data_logging: Si es True, habilita logging detallado de estructuras de datos.
    """
    # Registrar nivel personalizado TRACE
    logging.addLevelName(TRACE, "TRACE")
    
    # Método para logging a nivel TRACE
    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)
    
    # Añadir método trace a la clase Logger
    logging.Logger.trace = trace
    
    # Configuración básica
    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))  # Establecer al nivel más bajo requerido
    
    # Eliminar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    
    if enable_json_logs:
        console_formatter = JsonFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Handler de archivo (opcional)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        
        if enable_json_logs:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
            )
            
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configurar flag global para logging de datos
    global DATA_LOGGING_ENABLED
    DATA_LOGGING_ENABLED = data_logging
    
    logging.info(f"Logging configurado: console={logging.getLevelName(console_level)}, "
                f"file={logging.getLevelName(file_level) if log_file else 'deshabilitado'}, "
                f"json={enable_json_logs}, data_logging={data_logging}")

# Variable global para control de logging de datos
DATA_LOGGING_ENABLED = False

def get_log_level(level_str: str) -> int:
    """Convierte string de nivel de log a constante de logging."""
    levels = {
        "TRACE": TRACE,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

def log_data(logger, level: int, msg: str, data: Any, max_length: int = 10000) -> None:
    """
    Log de datos estructurados con soporte para objetos complejos y truncamiento.
    
    Args:
        logger: Logger de Python a utilizar
        level: Nivel de logging (ej. logging.INFO)
        msg: Mensaje descriptivo
        data: Datos a loggear (dict, list, object, etc.)
        max_length: Tamaño máximo de string para evitar logs enormes
    """
    if not DATA_LOGGING_ENABLED:
        return
    
    # Función custom para serializar objetos
    def custom_serializer(obj):
        if callable(obj):
            return f"<function: {obj.__name__}>"
        return str(obj)
    
    # Función recursiva para limpiar datos no serializables
    def clean_for_serialization(item):
        if callable(item):
            return f"<function: {getattr(item, '__name__', 'anonymous')}>"
        elif hasattr(item, '__dict__'):
            return {
                '__type__': item.__class__.__name__,
                **{k: clean_for_serialization(v) for k, v in item.__dict__.items() if not k.startswith('_')}
            }
        elif isinstance(item, dict):
            return {k: clean_for_serialization(v) for k, v in item.items()}
        elif isinstance(item, (list, tuple)):
            return [clean_for_serialization(i) for i in item]
        else:
            return item
    
    # Limpiar datos para serialización
    try:
        serialized = clean_for_serialization(data)
    except Exception as e:
        serialized = {"__error__": f"Error cleaning data: {str(e)}"}
    
    try:
        data_str = json.dumps(serialized, default=custom_serializer, indent=2)
        if len(data_str) > max_length:
            data_str = data_str[:max_length] + "... [truncado]"
    except (TypeError, OverflowError, ValueError) as e:
        data_str = f"{str(data)[:max_length]}... [no serializable: {str(e)}]"
    
    # Crear un registro con datos adicionales
    extra = {'data': serialized}
    logger.log(level, f"{msg}: {data_str}", extra=extra)

# Exponer helpers para facilitar el uso
def log_info_data(logger, msg: str, data: Any) -> None:
    log_data(logger, logging.INFO, msg, data)

def log_debug_data(logger, msg: str, data: Any) -> None:
    log_data(logger, logging.DEBUG, msg, data)

def log_trace_data(logger, msg: str, data: Any) -> None:
    log_data(logger, TRACE, msg, data) 