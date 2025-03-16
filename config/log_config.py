import logging
import os
import json
from datetime import datetime
import sys
import traceback

TRACE = 5  # Custom trace level

class JsonFormatter(logging.Formatter):
    """Formatter that outputs logs in structured JSON format."""
    def format(self, record):
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
        if hasattr(record, 'data') and record.data:
            log_record["data"] = record.data
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        try:
            return json.dumps(log_record, default=custom_json_default)
        except Exception as e:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": f"[JSON serialization error: {str(e)}] {record.getMessage()}",
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            })

def setup_logging(
    log_file: str = "learning_path.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_json_logs: bool = True,
    data_logging: bool = True
) -> None:
    logging.addLevelName(TRACE, "TRACE")
    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)
    logging.Logger.trace = trace
    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    if enable_json_logs:
        console_formatter = JsonFormatter()
    else:
        console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        if enable_json_logs:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    global DATA_LOGGING_ENABLED
    DATA_LOGGING_ENABLED = data_logging
    logging.info(f"Logging configured: console={logging.getLevelName(console_level)}, file={logging.getLevelName(file_level) if log_file else 'disabled'}, json={enable_json_logs}, data_logging={data_logging}")

DATA_LOGGING_ENABLED = False

def get_log_level(level_str: str) -> int:
    levels = {
        "TRACE": TRACE,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

def log_data(logger, level: int, msg: str, data, max_length: int = 10000) -> None:
    if not DATA_LOGGING_ENABLED:
        return
    def custom_serializer(obj):
        if callable(obj):
            return f"<function: {obj.__name__}>"
        return str(obj)
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
    try:
        serialized = clean_for_serialization(data)
    except Exception as e:
        serialized = {"__error__": f"Error cleaning data: {str(e)}"}
    try:
        data_str = json.dumps(serialized, default=custom_serializer, indent=2)
        if len(data_str) > max_length:
            data_str = data_str[:max_length] + "... [truncated]"
    except Exception as e:
        data_str = f"{str(data)[:max_length]}... [not serializable: {str(e)}]"
    extra = {'data': serialized}
    logger.log(level, f"{msg}: {data_str}", extra=extra)

def log_info_data(logger, msg: str, data) -> None:
    log_data(logger, logging.INFO, msg, data)

def log_debug_data(logger, msg: str, data) -> None:
    log_data(logger, logging.DEBUG, msg, data)

def log_trace_data(logger, msg: str, data) -> None:
    log_data(logger, get_log_level("TRACE"), msg, data)
