#!/usr/bin/env python3
"""
Debug Learning Path Generator

Esta herramienta ejecuta el generador de rutas de aprendizaje con opciones de
diagnóstico extendidas para depurar problemas como contenido faltante en submódulos.

Uso:
  python debug_learning_path.py "Tema de aprendizaje" --log-level DEBUG

Opciones de depuración disponibles:
  --log-level: Nivel de detalle para logging (TRACE, DEBUG, INFO, WARNING, ERROR)
  --log-file: Ubicación del archivo de logs
  --disable-json: Deshabilitar formato JSON en logs
  --disable-data-logging: Deshabilitar logging detallado de estructuras de datos
"""

import os
import sys
import json
import argparse
import asyncio
import importlib.util
from datetime import datetime

from main import generate_learning_path
from log_config import setup_logging, get_log_level

def parse_arguments():
    parser = argparse.ArgumentParser(description="Debug Learning Path Generator")
    
    # Argumentos principales
    parser.add_argument("topic", help="Tema para generar la ruta de aprendizaje")
    parser.add_argument("--parallel", type=int, default=2, 
                      help="Número de módulos a procesar en paralelo")
    parser.add_argument("--search-parallel", type=int, default=3, 
                      help="Número de búsquedas a ejecutar en paralelo")
    parser.add_argument("--submodule-parallel", type=int, default=2, 
                      help="Número de submódulos a procesar en paralelo")
    
    # Opciones de logging
    parser.add_argument("--log-level", choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="DEBUG", help="Nivel de detalle para logging")
    parser.add_argument("--log-file", default="debug_learning_path.log", 
                      help="Archivo de log")
    parser.add_argument("--disable-json", action="store_true", 
                      help="Deshabilitar formato JSON en logs")
    parser.add_argument("--disable-data-logging", action="store_true", 
                      help="Deshabilitar logging detallado de estructuras de datos")
    
    # Opciones de análisis post-ejecución
    parser.add_argument("--save-result", action="store_true", 
                      help="Guardar el resultado en un archivo JSON")
    parser.add_argument("--output-dir", default="debug_output", 
                      help="Directorio para guardar resultados")
    parser.add_argument("--analyze-logs", action="store_true", 
                      help="Ejecutar análisis automático de logs al finalizar")
    
    return parser.parse_args()

async def progress_callback(message: str):
    """Callback para mostrar progreso en tiempo real."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] PROGRESO: {message}")

def save_result(result, args):
    """Guardar el resultado en un archivo JSON."""
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = args.topic.replace(" ", "_").replace("/", "_")[:30]
    filename = f"{args.output_dir}/result_{safe_topic}_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Resultado guardado en: {filename}")
    return filename

def run_diagnostic(log_file):
    """Ejecutar la herramienta de diagnóstico en el archivo de log."""
    print(f"\n=== EJECUTANDO DIAGNÓSTICO DE LOGS ===")
    print(f"Analizando archivo: {log_file}")
    
    # Importar la herramienta de diagnóstico
    try:
        import diagnostic
        diagnostic.print_log_summary(diagnostic.load_log_file(log_file))
    except ImportError:
        print("No se pudo importar el módulo de diagnóstico.")
    except Exception as e:
        print(f"Error ejecutando diagnóstico: {str(e)}")

async def main():
    args = parse_arguments()
    
    # Configurar logging
    print(f"Configurando logging: nivel={args.log_level}, archivo={args.log_file}")
    setup_logging(
        log_file=args.log_file,
        console_level=get_log_level(args.log_level),
        file_level=get_log_level("DEBUG"),  # Siempre DEBUG en archivo para diagnóstico
        enable_json_logs=not args.disable_json,
        data_logging=not args.disable_data_logging
    )
    
    # Ejecutar generación de ruta
    print(f"\n=== INICIANDO GENERACIÓN DE RUTA DE APRENDIZAJE ===")
    print(f"Tema: {args.topic}")
    print(f"Configuración de paralelismo: módulos={args.parallel}, búsquedas={args.search_parallel}, submódulos={args.submodule_parallel}")
    
    start_time = datetime.now()
    
    try:
        result = await generate_learning_path(
            topic=args.topic,
            parallel_count=args.parallel,
            search_parallel_count=args.search_parallel,
            submodule_parallel_count=args.submodule_parallel,
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n=== GENERACIÓN COMPLETADA ===")
        print(f"Duración: {duration}")
        
        # Mostrar estadísticas básicas
        modules = result.get("modules", [])
        total_submodules = sum(len(module.get("submodules", [])) for module in modules)
        print(f"Módulos generados: {len(modules)}")
        print(f"Submódulos totales: {total_submodules}")
        
        # Comprobar contenido en submódulos
        empty_submodules = []
        for i, module in enumerate(modules):
            for j, submodule in enumerate(module.get("submodules", [])):
                if not submodule.get("content"):
                    empty_submodules.append((i+1, j+1, submodule.get("title")))
        
        if empty_submodules:
            print(f"\n⚠️ ALERTA: Se encontraron {len(empty_submodules)} submódulos sin contenido:")
            for module_idx, submodule_idx, title in empty_submodules:
                print(f"  - Módulo {module_idx}, Submódulo {submodule_idx}: {title}")
        else:
            print("\n✅ Todos los submódulos tienen contenido.")
        
        # Guardar resultado
        if args.save_result:
            result_file = save_result(result, args)
        
        # Ejecutar análisis de logs
        if args.analyze_logs:
            run_diagnostic(args.log_file)
        
        # Mostrar instrucciones finales
        print("\nPara ver un análisis detallado de los logs, ejecute:")
        print(f"python diagnostic.py {args.log_file} --summary")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 