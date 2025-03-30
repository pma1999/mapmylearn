import time
from typing import Dict, Tuple, List, Optional
import os
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Estructura de datos para almacenar el rate limiting
# {ip_address: [(timestamp1, endpoint1), (timestamp2, endpoint2), ...]}
request_history: Dict[str, List[Tuple[float, str]]] = {}

# Endpoints especialmente sensibles que requieren rate limiting más restrictivo
sensitive_endpoints = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh"
]

# Límites específicos para endpoints sensibles (solicitudes por ventana de tiempo)
sensitive_limits = {
    "/api/auth/login": 5,         # 5 intentos de login por minuto
    "/api/auth/register": 3,      # 3 intentos de registro por minuto
    "/api/auth/refresh": 10       # 10 renovaciones de token por minuto
}

def cleanup_old_requests(ip_address: str, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> None:
    """Elimina solicitudes antiguas fuera de la ventana de tiempo"""
    if ip_address not in request_history:
        return
    
    current_time = time.time()
    cutoff_time = current_time - window_seconds
    
    # Conservar solo las solicitudes dentro de la ventana de tiempo
    request_history[ip_address] = [
        (timestamp, endpoint) for timestamp, endpoint in request_history[ip_address]
        if timestamp > cutoff_time
    ]
    
    # Si no quedan solicitudes, eliminar la entrada completamente
    if not request_history[ip_address]:
        del request_history[ip_address]

def is_rate_limited(ip_address: str, endpoint: str) -> Tuple[bool, Optional[int]]:
    """
    Comprueba si una solicitud supera los límites de tasa.
    Devuelve (rate_limited, retry_after) donde retry_after son los segundos a esperar.
    """
    if not ENABLE_RATE_LIMITING:
        return False, None
    
    cleanup_old_requests(ip_address)
    
    # Si no hay historial previo para esta IP, definitivamente no está limitada
    if ip_address not in request_history:
        request_history[ip_address] = []
        return False, None
    
    current_time = time.time()
    
    # Determinar el límite basado en el endpoint
    request_limit = RATE_LIMIT_REQUESTS  # Límite predeterminado
    
    # Comprobar si es un endpoint sensible
    for sensitive_endpoint in sensitive_endpoints:
        if endpoint.startswith(sensitive_endpoint):
            endpoint_key = next((key for key in sensitive_limits.keys() 
                              if endpoint.startswith(key)), None)
            if endpoint_key:
                request_limit = sensitive_limits[endpoint_key]
                break
    
    # Contar solicitudes recientes para este endpoint específico
    relevant_requests = [
        timestamp for timestamp, req_endpoint in request_history[ip_address]
        if endpoint.startswith(req_endpoint.split("?")[0])  # Ignorar parámetros de consulta
    ]
    
    if len(relevant_requests) >= request_limit:
        # Calculamos cuándo podrá realizar una nueva solicitud
        oldest_timestamp = min(relevant_requests) if relevant_requests else current_time
        retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (current_time - oldest_timestamp)) + 1
        
        # Registrar intento bloqueado
        logger.warning(f"Rate limit exceeded for IP {ip_address} on endpoint {endpoint}. "
                       f"Requests: {len(relevant_requests)}/{request_limit}")
        
        return True, max(0, retry_after)
    
    # Añadir esta solicitud al historial
    request_history[ip_address].append((current_time, endpoint))
    return False, None

async def rate_limiting_middleware(request: Request, call_next):
    """Middleware para aplicar límites de tasa a las solicitudes"""
    # Extraer dirección IP del cliente
    ip_address = request.client.host if request.client else "unknown"
    
    # Extraer el endpoint siendo accedido
    endpoint = request.url.path
    
    # Comprobar si está limitada
    is_limited, retry_after = is_rate_limited(ip_address, endpoint)
    
    if is_limited:
        headers = {"Retry-After": str(retry_after)}
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            headers=headers
        )
    
    # Proceder con la solicitud si no está limitada
    return await call_next(request) 