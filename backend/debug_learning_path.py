#!/usr/bin/env python3
"""
Debug Course Generator

Usage:
  python debug_learning_path.py "Learning Topic" --log-level DEBUG

Provides extended diagnostic options to debug the course generation process.
"""

import logging
import os
import sys
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import argparse
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

# Project imports
from backend.main import generate_learning_path
from backend.config.log_config import setup_logging, get_log_level

def parse_arguments():
    parser = argparse.ArgumentParser(description="Debug Course Generator")
    parser.add_argument("topic", help="Topic for course generation")
    parser.add_argument("--parallel", type=int, default=2, help="Number of modules in parallel")
    parser.add_argument("--search-parallel", type=int, default=3, help="Number of parallel searches")
    parser.add_argument("--submodule-parallel", type=int, default=2, help="Number of parallel submodules")
    parser.add_argument("--log-level", choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"], default="DEBUG", help="Logging level")
    parser.add_argument("--log-file", default="debug_learning_path.log", help="Log file location")
    parser.add_argument("--disable-json", action="store_true", help="Disable JSON log formatting")
    parser.add_argument("--disable-data-logging", action="store_true", help="Disable detailed data logging")
    parser.add_argument("--save-result", action="store_true", help="Save the result in a JSON file")
    parser.add_argument("--output-dir", default="debug_output", help="Directory to save results")
    parser.add_argument("--analyze-logs", action="store_true", help="Run automatic log analysis after execution")
    return parser.parse_args()

async def progress_callback(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] PROGRESS: {message}")

def save_result(result, args):
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = args.topic.replace(" ", "_")[:30]
    filename = f"{args.output_dir}/result_{safe_topic}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Result saved in: {filename}")
    return filename

def run_diagnostic(log_file):
    print(f"\n=== RUNNING LOG DIAGNOSTIC ===")
    print(f"Analyzing file: {log_file}")
    try:
        import backend.diagnostic as diagnostic
        diagnostic.print_log_summary(diagnostic.load_log_file(log_file))
    except ImportError:
        print("Diagnostic module not found.")
    except Exception as e:
        print(f"Error during diagnostic: {str(e)}")

async def main():
    args = parse_arguments()
    print(f"Configuring logging: level={args.log_level}, file={args.log_file}")
    setup_logging(
        log_file=args.log_file,
        console_level=get_log_level(args.log_level),
        file_level=get_log_level("DEBUG"),
        enable_json_logs=not args.disable_json,
        data_logging=not args.disable_data_logging
    )
    print(f"\n=== STARTING LEARNING PATH GENERATION ===")
    print(f"Topic: {args.topic}")
    print(f"Parallel config: modules={args.parallel}, searches={args.search_parallel}, submodules={args.submodule_parallel}")
    start_time = datetime.now()
    try:
        result = await generate_learning_path(
            topic=args.topic,
            parallel_count=args.parallel,
            search_parallel_count=args.search_parallel,
            submodule_parallel_count=args.submodule_parallel,
            progress_callback=progress_callback
        )
        duration = datetime.now() - start_time
        print(f"\n=== GENERATION COMPLETED in {duration} ===")
        modules = result.get("modules", [])
        print(f"Modules generated: {len(modules)}")
        empty_submodules = []
        for i, module in enumerate(modules):
            for j, sub in enumerate(module.get("submodules", [])):
                if not sub.get("content"):
                    empty_submodules.append((i+1, j+1, sub.get("title")))
        if empty_submodules:
            print(f"\n⚠️ {len(empty_submodules)} submodules with no content found:")
            for mod_idx, sub_idx, title in empty_submodules:
                print(f"  - Module {mod_idx}, Submodule {sub_idx}: {title}")
        else:
            print("\n✅ All submodules have content.")
        if args.save_result:
            save_result(result, args)
        if args.analyze_logs:
            run_diagnostic(args.log_file)
        print("\nTo view detailed log analysis, run:")
        print(f"python diagnostic.py {args.log_file} --summary")
    except Exception as e:
        print(f"\n❌ Error during generation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
