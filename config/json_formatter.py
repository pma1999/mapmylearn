import json
import traceback
from datetime import datetime

class JsonFormatter:
    """Converts log records into structured JSON."""
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
