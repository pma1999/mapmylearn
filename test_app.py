"""
Test script for the Learning Path Generator.
This script verifies that all components are working correctly.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def test_imports():
    """Test that all required packages can be imported."""
    try:
        import langchain
        import langgraph
        import pydantic
        import streamlit
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_build_graph():
    """Test that the graph can be built successfully."""
    try:
        from learning_path_generator import build_graph
        graph = build_graph()
        print("✅ Graph built successfully")
        # Print the nodes if available
        try:
            nodes = list(graph.graph.nodes)
            print(f"Graph nodes: {nodes}")
        except:
            print("Could not retrieve graph nodes, but graph was built")
        return True
    except Exception as e:
        print(f"❌ Error building graph: {e}")
        return False

def test_tavily_api():
    """Test that the Tavily API key is configured."""
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        print("✅ Tavily API key is configured")
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            search_tool = TavilySearchResults(max_results=1)
            print("✅ Tavily search tool initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing Tavily search tool: {e}")
            return False
    else:
        print("❌ Tavily API key is not set")
        print("Note: You'll need to provide the Tavily API key in the web interface")
        # Return True to avoid failing the test
        return True

def test_openai_api():
    """Test that the OpenAI API key is configured."""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        print("✅ OpenAI API key is configured")
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo")
            print("✅ OpenAI LLM initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing OpenAI LLM: {e}")
            return False
    else:
        print("❌ OpenAI API key is not set")
        print("Note: You'll need to provide the OpenAI API key in the web interface")
        # Return True to avoid failing the test
        return True

def test_streamlit_app():
    """Test that the Streamlit app can be imported."""
    try:
        import app
        print("✅ Streamlit app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing Streamlit app: {e}")
        return False

def run_tests():
    """Run all tests and report results."""
    print("🧪 Running Learning Path Generator tests...\n")
    
    tests = [
        ("Package imports", test_imports),
        ("Graph building", test_build_graph),
        ("Tavily API", test_tavily_api),
        ("OpenAI API", test_openai_api),
        ("Streamlit app", test_streamlit_app)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing: {name}")
        try:
            result = test_func()
            results.append(result)
            print("")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append(False)
            print("")
    
    # Print summary
    print("\n===== TEST SUMMARY =====")
    passed = sum(results)
    total = len(tests)
    print(f"Passed: {passed}/{total} tests")
    
    for i, (name, _) in enumerate(tests):
        status = "PASS" if results[i] else "FAIL"
        print(f"{status}: {name}")
    
    # Print final message
    if all(results):
        print("\n✅ All tests passed! The Learning Path Generator is ready to use.")
        print("To start the application, run: python run.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all(results)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 