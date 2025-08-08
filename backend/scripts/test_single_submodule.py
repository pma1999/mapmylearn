import os
import json
from pathlib import Path

from dotenv import load_dotenv

from backend.main import build_learning_path


def main():
    # Load .env from backend or project root
    backend_env = Path(__file__).resolve().parents[1] / '.env'
    load_dotenv(dotenv_path=backend_env)
    if not os.getenv('GOOGLE_API_KEY'):
        load_dotenv(dotenv_path=Path('.') / '.env')

    topic = os.environ.get('TEST_TOPIC', 'Contexto histórico y político de EEUU previo a Donald Trump')

    result = build_learning_path(
        topic=topic,
        parallel_count=1,
        search_parallel_count=2,
        submodule_parallel_count=1,
        desired_module_count=1,
        desired_submodule_count=1,
        language=os.environ.get('TEST_LANG', 'es'),
        explanation_style='standard',
    )

    modules = result.get('modules', [])
    print(f"Modules: {len(modules)}")
    if not modules:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    submodules = modules[0].get('submodules', [])
    print(f"Submodules in module 1: {len(submodules)}")
    if not submodules:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    sub = submodules[0]
    title = sub.get('title', 'Untitled')
    print(f"\n=== Submodule Title ===\n{title}")

    content = sub.get('content', '')
    print(f"\n=== Content ===\n{content}")

    # Quick check for image markdown presence
    has_image = '!["' in content or '![' in content
    commons = 'Wikimedia Commons' in content
    print(f"\nImage present: {has_image}; Attribution present: {commons}")


if __name__ == '__main__':
    main()
