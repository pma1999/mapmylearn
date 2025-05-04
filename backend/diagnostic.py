#!/usr/bin/env python3
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

def load_log_file(log_file: str) -> List[Dict[str, Any]]:
    if not os.path.exists(log_file):
        print(f"Error: {log_file} does not exist.")
        return []
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                entries.append({"raw": line.strip()})
    return entries

def filter_logs(entries: List[Dict[str, Any]], level: Optional[str] = None, 
                module: Optional[str] = None, contains: Optional[str] = None) -> List[Dict[str, Any]]:
    filtered = entries
    if level:
        filtered = [e for e in filtered if e.get("level") == level]
    if module:
        filtered = [e for e in filtered if e.get("module") == module]
    if contains:
        filtered = [e for e in filtered if contains.lower() in json.dumps(e).lower()]
    return filtered

def print_log_summary(entries: List[Dict[str, Any]]) -> None:
    if not entries:
        print("No log entries to display.")
        return
    level_counts = {}
    for entry in entries:
        level = entry.get("level", "UNKNOWN")
        level_counts[level] = level_counts.get(level, 0) + 1
    print("\n=== LOG SUMMARY ===")
    print(f"Total entries: {len(entries)}")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count}")
    print("\n=== ERRORS & WARNINGS ===")
    for entry in entries:
        if entry.get("level") in ["ERROR", "WARNING"]:
            timestamp = entry.get("timestamp", "")
            message = entry.get("message", "")
            print(f"[{timestamp}] {entry.get('level')}: {message}")
    print("\n=== FINAL DATA STRUCTURE ===")
    final_learning_path = None
    for entry in reversed(entries):
        if "final course structure" in entry.get("message", "").lower():
            final_learning_path = entry.get("data")
            break
    if not final_learning_path:
        print("Final course structure not found in logs.")
        return
    print(f"Topic: {final_learning_path.get('topic', 'N/A')}")
    print(f"Number of modules: {len(final_learning_path.get('modules', []))}")
    for i, module in enumerate(final_learning_path.get("modules", [])):
        print(f"\nModule {i+1}: {module.get('title', 'No title')}")
        submodules = module.get("submodules", [])
        print(f"  Submodules: {len(submodules)}")
        for j, submodule in enumerate(submodules):
            content = submodule.get("content", "")
            status = "OK" if len(content) > 0 else "NO CONTENT"
            print(f"  Submodule {j+1}: {submodule.get('title', 'No title')} - {len(content)} chars - {status}")

def main():
    parser = argparse.ArgumentParser(description="Diagnostic tool for course logs")
    parser.add_argument("log_file", help="Path to log file")
    parser.add_argument("--level", help="Filter by log level (INFO, DEBUG, etc.)")
    parser.add_argument("--module", help="Filter by module")
    parser.add_argument("--contains", help="Filter by text")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
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
        print(f"\nResults saved in {args.output}")

if __name__ == "__main__":
    main()
