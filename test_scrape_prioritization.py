import asyncio
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScrapeTest")

# --- Attempt to import necessary components ---
try:
    from backend.services.services import perform_search_and_scrape, TARGET_SUCCESSFUL_SCRAPES
    from backend.services.key_provider import BraveKeyProvider
    from backend.models.models import SearchServiceResult
except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}")
    logger.error("Please ensure the script is run from the workspace root and backend modules are accessible.")
    exit(1)

# --- Load Environment Variables ---
# Specify the correct path to the .env file
DOTENV_PATH = os.path.join('backend', '.env') 
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
    logger.info(f"Loaded environment variables from {DOTENV_PATH}")
else:
    logger.warning(f".env file not found at {DOTENV_PATH}. Relying on system environment variables.")
    # Attempt default load_dotenv() which might find it elsewhere or do nothing
    load_dotenv()

async def run_test_case(provider: BraveKeyProvider, query: str, max_results_cap: int, case_name: str):
    """Runs a single test case and prints results."""
    logger.info(f"--- Running Test Case: {case_name} ---")
    logger.info(f"Query: '{query}', Max Results Cap: {max_results_cap}, Target Success: {TARGET_SUCCESSFUL_SCRAPES}")

    try:
        result: SearchServiceResult = await perform_search_and_scrape(
            query=query,
            brave_key_provider=provider,
            max_results=max_results_cap,
            scrape_timeout=15 # Slightly longer timeout for testing resilience
        )

        successful_scrapes = sum(1 for r in result.results if r.scraped_content)
        failed_scrapes = sum(1 for r in result.results if r.scrape_error)
        total_results_returned = len(result.results)

        logger.info(f"Result Summary:")
        logger.info(f"  - Total Results Returned: {total_results_returned}")
        logger.info(f"  - Successful Scrapes: {successful_scrapes}")
        logger.info(f"  - Failed Scrapes (with error/snippet): {failed_scrapes}")

        # --- Assertions ---
        passed = True
        # 1. Check total results cap
        if total_results_returned > max_results_cap:
            logger.error(f"Assertion Failed: Returned {total_results_returned} results, exceeding max_results_cap of {max_results_cap}.")
            passed = False
        else:
            logger.info(f"Assertion Passed: Returned {total_results_returned} results <= max_results_cap ({max_results_cap}).")

        # 2. Check successful scrape count (relative to target and cap)
        expected_min_successful = 0 # Can be 0 if all fail
        # We expect *up to* TARGET_SUCCESSFUL_SCRAPES, but capped by max_results_cap
        expected_max_successful = min(TARGET_SUCCESSFUL_SCRAPES, max_results_cap)

        # If the *actual* number of successful scrapes found within fetch_count was less than the target/cap,
        # the returned count should match that actual number.
        # This assertion mainly checks if prioritization worked *given the available successful scrapes*.
        # We can't strictly assert `successful_scrapes == expected_max_successful` because the underlying
        # scraping might genuinely fail more often than the target.
        # A better check is if the number of successful scrapes seems reasonable given the target/cap.
        if successful_scrapes > expected_max_successful:
             logger.warning(f"Observation: Returned {successful_scrapes} successful scrapes, which is more than the expected max based on target/cap ({expected_max_successful}). This is okay if prioritization placed them within max_results_cap.")
             # It's possible if target=3, max_results=5, and first 5 were successful.

        if successful_scrapes <= max_results_cap:
             logger.info(f"Assertion Passed: Number of successful scrapes ({successful_scrapes}) is within max_results_cap ({max_results_cap}).")
        else:
             logger.error(f"Assertion Failed: Number of successful scrapes ({successful_scrapes}) exceeds max_results_cap ({max_results_cap}).")
             passed = False


        # 3. Check consistency: successful + failed should equal total returned
        if successful_scrapes + failed_scrapes != total_results_returned:
            logger.error(f"Assertion Failed: Sum of successful ({successful_scrapes}) and failed ({failed_scrapes}) scrapes does not equal total returned ({total_results_returned}).")
            passed = False
        else:
            logger.info(f"Assertion Passed: Successful ({successful_scrapes}) + Failed ({failed_scrapes}) = Total ({total_results_returned}).")


        logger.info(f"Case '{case_name}' Result: {'PASS' if passed else 'FAIL'}")
        print("-" * 30) # Separator
        return passed

    except Exception as e:
        logger.exception(f"Error running test case '{case_name}': {e}")
        logger.info(f"Case '{case_name}' Result: ERROR")
        print("-" * 30) # Separator
        return False


async def main():
    # --- Instantiate Key Provider ---
    # Use the correct environment variable name
    brave_api_key = os.environ.get("BRAVE_API_KEY") 
    if not brave_api_key:
        logger.error("BRAVE_API_KEY not found in environment variables. Cannot run tests.")
        return

    # Assuming BraveKeyProvider can be instantiated like this or similarly
    # If it needs more complex setup, adjust here.
    try:
        # You might need to adjust instantiation based on BraveKeyProvider's __init__
        # Passing the key directly or letting it load from env if designed that way.
        # provider = BraveKeyProvider(api_key=brave_api_key)
        # It likely loads the key from the environment automatically
        provider = BraveKeyProvider()
        # Test the key validity if possible (optional)
        # is_valid, msg = await provider.validate_key()
        # if not is_valid:
    except Exception as e:
        logger.error(f"Failed to instantiate BraveKeyProvider: {e}")
        return

    # --- Define Test Cases ---
    test_cases = [
        {"name": "Case 1: Likely Enough Success", "query": "python requests library tutorial", "max_results": 5},
        {"name": "Case 2: Mixed Success/Fail (News/Protected)", "query": "latest advancements large language models news", "max_results": 5},
        {"name": "Case 3: Very Low Max Results", "query": "python documentation list methods", "max_results": 2},
        {"name": "Case 4: Higher Max Results", "query": "how does https work explained", "max_results": 7},
         {"name": "Case 5: Potentially Difficult PDFs", "query": "machine learning research papers pdf", "max_results": 5},
    ]

    results = []
    for case in test_cases:
        passed = await run_test_case(provider, case["query"], case["max_results"], case["name"])
        results.append(passed)

    # --- Final Summary ---
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r is True)
    failed_cases = sum(1 for r in results if r is False)
    error_cases = total_cases - passed_cases - failed_cases # Should be 0 if no exceptions

    logger.info("========== Test Summary ==========")
    logger.info(f"Total Cases: {total_cases}")
    logger.info(f"Passed: {passed_cases}")
    logger.info(f"Failed/Error: {failed_cases + error_cases}")
    logger.info("================================")

if __name__ == "__main__":
    asyncio.run(main()) 