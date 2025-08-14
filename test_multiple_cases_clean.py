#!/usr/bin/env python3
"""
Comprehensive Multiple Case Test - Enhanced Image Search Analysis
Tests multiple challenging cases to identify failure patterns and improve success rates.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path for imports
sys.path.append('.')
sys.path.append('./backend')

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import the enhanced functionality
from backend.models.models import EnhancedModule, Submodule
from backend.core.submodules.content_enrichment import _find_relevant_image_with_retry
from backend.services.key_provider import GoogleKeyProvider
import os

class ComprehensiveTester:
    """Tests enhanced image search on multiple challenging cases."""
    
    def __init__(self):
        self.google_key_provider = self._setup_google_key_provider()
        self.success_count = 0
        self.total_count = 0
        
    def _setup_google_key_provider(self):
        """Set up Google key provider from environment."""
        try:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                print("ERROR: GOOGLE_API_KEY not found in environment")
                return None
            print(f"SUCCESS: Google API Key found: {google_api_key[:10]}...")
            return GoogleKeyProvider(google_api_key)
        except Exception as e:
            print(f"ERROR: Error setting up Google Key Provider: {e}")
            return None
    
    def _create_test_state(self, topic: str) -> Dict[str, Any]:
        """Create test state configuration."""
        return {
            "user_topic": topic,
            "language": "es",
            "google_key_provider": self.google_key_provider,
            "user": {"id": "test_user"},
            "enhanced_image_search_enabled": True,
            "max_image_search_attempts": 3,
            "images_enrichment_enabled": True,
            "images_per_submodule": 5,
        }
    
    async def test_case(self, case_name: str, user_topic: str, module_title: str, 
                       submodule_title: str, section_heading: str, topic_hint: str) -> Dict[str, Any]:
        """Test a single challenging case."""
        print(f"\n{'='*80}")
        print(f"TEST CASE: {case_name}")
        print(f"Challenge: {topic_hint}")
        print(f"{'='*80}")
        
        state = self._create_test_state(user_topic)
        module = EnhancedModule(title=module_title, description="Test module")
        submodule = Submodule(title=submodule_title, description="Test submodule")
        
        print(f"Parameters:")
        print(f"   Topic: {user_topic}")
        print(f"   Module: {module_title}")
        print(f"   Submodule: {submodule_title}")
        print(f"   Section: {section_heading}")
        print(f"   Hint: {topic_hint}")
        
        self.total_count += 1
        
        try:
            result = await _find_relevant_image_with_retry(
                state, module, submodule, section_heading, 
                exclude_urls=set(), topic_hint=topic_hint, 
                max_attempts=3
            )
            
            if result:
                self.success_count += 1
                print(f"SUCCESS: Found image!")
                print(f"   Title: {result.get('title', 'N/A')[:60]}...")
                print(f"   Caption: {result.get('caption', 'N/A')[:80]}...")
                return {"success": True, "case": case_name, "result": result}
            else:
                print(f"FAILURE: No image found")
                return {"success": False, "case": case_name, "failure_reason": "No relevant image found"}
                
        except Exception as e:
            print(f"ERROR: {e}")
            return {"success": False, "case": case_name, "failure_reason": str(e)}

    async def run_comprehensive_test(self):
        """Run multiple challenging test cases to identify failure patterns."""
        print("COMPREHENSIVE ENHANCED IMAGE SEARCH TEST")
        print("Testing multiple challenging cases to identify improvement areas")
        
        if not self.google_key_provider:
            print("ERROR: Cannot run test without Google API key")
            return False
        
        # Define challenging test cases that might fail
        test_cases = [
            {
                "name": "Abstract Philosophy",
                "user_topic": "Teoría Crítica Frankfurtiana",
                "module_title": "Filosofía Social Contemporánea",
                "submodule_title": "Escuela de Fráncfort",
                "section_heading": "Dialéctica Negativa de Adorno",
                "topic_hint": "dialéctica negativa teoría crítica"
            },
            {
                "name": "Mathematical Concepts",
                "user_topic": "Topología Diferencial",
                "module_title": "Matemáticas Avanzadas",
                "submodule_title": "Variedades Diferenciables",
                "section_heading": "Teoremas de Stokes Generalizados",
                "topic_hint": "topología diferencial variedades"
            },
            {
                "name": "Economic Theory",
                "user_topic": "Macroeconomía Keynesiana",
                "module_title": "Teorías Económicas",
                "submodule_title": "Políticas Fiscales",
                "section_heading": "Multiplicadores de Gasto Público",
                "topic_hint": "multiplicadores keynesianos gasto público"
            },
            {
                "name": "Psychological Concepts",
                "user_topic": "Psicología Cognitiva",
                "module_title": "Procesos Mentales",
                "submodule_title": "Memoria de Trabajo",
                "section_heading": "Modelo de Baddeley y Hitch",
                "topic_hint": "memoria trabajo modelo Baddeley"
            },
            {
                "name": "Literary Theory",
                "user_topic": "Narratología Estructuralista",
                "module_title": "Análisis Literario",
                "submodule_title": "Estructuras Narrativas",
                "section_heading": "Funciones de Propp en el Relato",
                "topic_hint": "funciones Propp narratología"
            },
            {
                "name": "Computer Science Theory",
                "user_topic": "Complejidad Computacional",
                "module_title": "Ciencias de la Computación",
                "submodule_title": "Clases de Complejidad",
                "section_heading": "Problemas NP-Completos",
                "topic_hint": "NP completo complejidad computacional"
            }
        ]
        
        results = []
        
        for case in test_cases:
            result = await self.test_case(
                case["name"], case["user_topic"], case["module_title"],
                case["submodule_title"], case["section_heading"], case["topic_hint"]
            )
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Analyze results
        print(f"\n{'='*90}")
        print("COMPREHENSIVE TEST RESULTS ANALYSIS")
        print(f"{'='*90}")
        
        success_rate = (self.success_count / self.total_count) * 100 if self.total_count > 0 else 0
        print(f"Overall Success Rate: {self.success_count}/{self.total_count} ({success_rate:.1f}%)")
        
        print(f"\nIndividual Results:")
        for result in results:
            status = "SUCCESS" if result["success"] else "FAILURE"
            print(f"   {status}: {result['case']}")
            if not result["success"]:
                print(f"      Reason: {result.get('failure_reason', 'Unknown')}")
        
        # Identify patterns in failures
        failures = [r for r in results if not r["success"]]
        if failures:
            print(f"\nFAILURE PATTERN ANALYSIS:")
            print(f"   Failed cases: {len(failures)}/{len(results)}")
            print(f"   Common issue: Abstract concepts without clear biographical/visual pivots")
            print(f"   Improvement needed: More aggressive alternative query generation")
        
        if success_rate < 80:  # If less than 80% success rate
            print(f"\nWARNING: SUCCESS RATE TOO LOW: {success_rate:.1f}%")
            print(f"    REQUIRES PROMPT IMPROVEMENT")
            return False
        else:
            print(f"\nSUCCESS RATE ACCEPTABLE: {success_rate:.1f}%")
            return True

async def main():
    """Main test execution function."""
    print("Enhanced Image Search - Comprehensive Case Analysis")
    print("Testing multiple challenging scenarios to identify improvement areas")
    
    tester = ComprehensiveTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\nComprehensive test shows acceptable success rates!")
    else:
        print("\nWARNING: Comprehensive test shows need for prompt improvements")
        print("Will proceed to enhance prompts based on failure patterns...")

if __name__ == "__main__":
    asyncio.run(main())
