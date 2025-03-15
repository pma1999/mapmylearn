#!/usr/bin/env python3
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

def load_log_file(log_file: str) -> List[Dict[str, Any]]:
    """Carga un archivo de log JSON y devuelve las entradas."""
    if not os.path.exists(log_file):
        print(f"Error: El archivo {log_file} no existe.")
        return []
    
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                # Para logs que no están en formato JSON
                entries.append({"raw": line.strip()})
    
    return entries

def filter_logs(entries: List[Dict[str, Any]], level: Optional[str] = None, 
                module: Optional[str] = None, contains: Optional[str] = None) -> List[Dict[str, Any]]:
    """Filtra las entradas de log según criterios."""
    filtered = entries
    
    if level:
        filtered = [e for e in filtered if e.get("level") == level]
    
    if module:
        filtered = [e for e in filtered if e.get("module") == module]
    
    if contains:
        filtered = [e for e in filtered if contains.lower() in json.dumps(e).lower()]
    
    return filtered

def print_log_summary(entries: List[Dict[str, Any]]) -> None:
    """Imprime un resumen de las entradas de log."""
    if not entries:
        print("No hay entradas de log para mostrar.")
        return
    
    # Contar por nivel
    level_counts = {}
    for entry in entries:
        level = entry.get("level", "UNKNOWN")
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print("\n=== RESUMEN DE LOGS ===")
    print(f"Total de entradas: {len(entries)}")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count}")
    
    # Encontrar errores y advertencias relevantes
    print("\n=== ERRORES Y ADVERTENCIAS DESTACADAS ===")
    for entry in entries:
        if entry.get("level") in ["ERROR", "WARNING"]:
            timestamp = entry.get("timestamp", "")
            message = entry.get("message", "")
            print(f"[{timestamp}] {entry.get('level')}: {message}")
    
    # Analizar estructura de datos final
    print("\n=== ANÁLISIS DE ESTRUCTURA DE DATOS FINAL ===")
    final_learning_path = None
    
    for entry in reversed(entries):  # Buscar desde el final
        if "final learning path structure" in entry.get("message", "").lower():
            final_learning_path = entry.get("data")
            break
    
    if not final_learning_path:
        print("No se encontró la estructura final de la ruta de aprendizaje en los logs.")
        return
    
    print(f"Tema: {final_learning_path.get('topic', 'No disponible')}")
    print(f"Número de módulos: {len(final_learning_path.get('modules', []))}")
    
    for i, module in enumerate(final_learning_path.get("modules", [])):
        print(f"\nMódulo {i+1}: {module.get('title', 'Sin título')}")
        submodules = module.get("submodules", [])
        print(f"  Submódulos: {len(submodules)}")
        
        for j, submodule in enumerate(submodules):
            content = submodule.get("content", "")
            content_length = len(content) if content else 0
            status = "OK" if content_length > 0 else "SIN CONTENIDO"
            print(f"  Submódulo {j+1}: {submodule.get('title', 'Sin título')} - {content_length} caracteres - {status}")

def main():
    parser = argparse.ArgumentParser(description="Herramienta de diagnóstico para logs de rutas de aprendizaje")
    parser.add_argument("log_file", help="Ruta al archivo de log")
    parser.add_argument("--level", help="Filtrar por nivel (INFO, DEBUG, ERROR, etc.)")
    parser.add_argument("--module", help="Filtrar por módulo")
    parser.add_argument("--contains", help="Filtrar por texto contenido")
    parser.add_argument("--output", help="Guardar resultado en archivo")
    parser.add_argument("--summary", action="store_true", help="Mostrar solo el resumen")
    
    args = parser.parse_args()
    
    entries = load_log_file(args.log_file)
    filtered = filter_logs(entries, args.level, args.module, args.contains)
    
    if args.summary:
        print_log_summary(filtered)
    else:
        for entry in filtered:
            print(json.dumps(entry, indent=2))
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2)
        print(f"\nResultados guardados en {args.output}")

if __name__ == "__main__":
    main() 