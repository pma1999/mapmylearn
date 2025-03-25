import asyncio
import json
import time
import logging
from typing import Dict, Any, List
from backend.models.models import SearchQuery
from backend.core.graph_nodes.initial_flow import execute_single_search, execute_web_searches
from backend.services.key_provider import PerplexityKeyProvider
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def test_search_execution():
    """
    Prueba la ejecución en paralelo de las búsquedas.
    
    Compara la ejecución secuencial y en paralelo para mostrar la mejora de rendimiento.
    """
    # Crear consultas de búsqueda de prueba
    search_queries = [
        SearchQuery(keywords=f"Python programming best practices part {i}", 
                   rationale=f"To learn about best practices in Python programming (part {i})")
        for i in range(1, 6)  # 5 consultas de búsqueda
    ]
    
    # Obtener la clave API de Perplexity del entorno
    pplx_api_key = os.getenv("PPLX_API_KEY")
    if not pplx_api_key:
        logger.error("PPLX_API_KEY no está establecida en el entorno")
        return
    
    # Crear un proveedor de clave para Perplexity
    pplx_provider = PerplexityKeyProvider(pplx_api_key)
    
    # Crear el estado para la prueba
    state = {
        "search_queries": search_queries,
        "pplx_key_provider": pplx_provider,
        "search_parallel_count": 5  # Ejecutar todas las consultas en paralelo
    }
    
    # Definir una función de callback para mostrar el progreso
    async def progress_callback(message: str):
        logger.info(f"Progreso: {message}")
    
    state["progress_callback"] = progress_callback
    
    # Prueba 1: Ejecución en paralelo
    logger.info("Iniciando prueba de ejecución en paralelo...")
    start_time = time.time()
    result = await execute_web_searches(state)
    end_time = time.time()
    parallel_time = end_time - start_time
    logger.info(f"Ejecución en paralelo completada en {parallel_time:.2f} segundos")
    
    # Prueba 2: Ejecución secuencial para comparar
    logger.info("Iniciando prueba de ejecución secuencial...")
    start_time = time.time()
    sequential_results = []
    for query in search_queries:
        result = await execute_single_search(query, key_provider=pplx_provider)
        sequential_results.append(result)
    end_time = time.time()
    sequential_time = end_time - start_time
    logger.info(f"Ejecución secuencial completada en {sequential_time:.2f} segundos")
    
    # Mostrar la comparación
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    logger.info(f"Aceleración: {speedup:.2f}x más rápido con ejecución en paralelo")
    
    return {
        "parallel_time": parallel_time,
        "sequential_time": sequential_time,
        "speedup": speedup
    }

async def main():
    """Función principal para ejecutar la prueba."""
    try:
        results = await test_search_execution()
        if results:
            logger.info("Resultados de la prueba:")
            logger.info(f"Tiempo en paralelo: {results['parallel_time']:.2f} segundos")
            logger.info(f"Tiempo secuencial: {results['sequential_time']:.2f} segundos")
            logger.info(f"Aceleración: {results['speedup']:.2f}x")
    except Exception as e:
        logger.exception(f"Error durante la prueba: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 