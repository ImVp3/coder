import os
import sys
import unittest
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Add project root to sys.path to allow importing core modules

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Now import the necessary modules
from core.graph.utils.routing import decide_to_route
from langchain_core.messages import HumanMessage

# --- Test Class ---

TEST_MODEL = "gemini-2.0-flash-lite"

# Skip tests if the required API key is not found
API_KEY_PRESENT = bool(os.getenv("GOOGLE_API_KEY")) 

@unittest.skipIf(not API_KEY_PRESENT, f"API Key (e.g., GOOGLE_API_KEY) not found in environment variables. Skipping integration tests for model {TEST_MODEL}.")
class TestDecideToRouteIntegration(unittest.TestCase):

    def test_route_to_complex_generation(self):
        """
        Test if a query requiring external libraries or complex logic routes to COMPLEX_GENERATION.
        """
        print(f"\nRunning test: test_route_to_complex_generation with model {TEST_MODEL}")
        query_content = "Generate a Python script using pandas to read 'data.csv' and plot a histogram of the 'value' column using matplotlib."
        state = {
            "messages": [HumanMessage(content=query_content)]
            # Other state fields are not used by decide_to_route
        }
        expected_route = "COMPLEX_GENERATION"

        # --- Act ---
        actual_route = decide_to_route(state, model=TEST_MODEL)
        print(f"Query: '{query_content}'")
        print(f"Expected: {expected_route}, Got: {actual_route}")

        # --- Assert ---
        # LLM outputs can sometimes have minor variations (like extra spaces or case changes)
        # It's safer to check containment or use lower() if strict matching isn't required by the downstream logic.
        # However, the prompt asks for *only* the one word, so assertEqual is reasonable here.
        self.assertEqual(actual_route.strip(), expected_route)

    def test_route_to_simple_generation(self):
        """
        Test if a query for simple code without external imports routes to GENERATION.
        """
        print(f"\nRunning test: test_route_to_simple_generation with model {TEST_MODEL}")
        query_content = "Write a Python function that takes two numbers and returns their sum."
        state = {
            "messages": [HumanMessage(content=query_content)]
        }
        expected_route = "GENERATION"

        # --- Act ---
        actual_route = decide_to_route(state, model=TEST_MODEL)
        print(f"Query: '{query_content}'")
        print(f"Expected: {expected_route}, Got: {actual_route}")

        # --- Assert ---
        self.assertEqual(actual_route.strip(), expected_route)

    def test_route_to_default(self):
        """
        Test if a casual or non-coding question routes to DEFAULT.
        """
        print(f"\nRunning test: test_route_to_default with model {TEST_MODEL}")
        query_content = "Hello, how are you today?"
        state = {
            "messages": [HumanMessage(content=query_content)]
        }
        expected_route = "DEFAULT"

        # --- Act ---
        actual_route = decide_to_route(state, model=TEST_MODEL)
        print(f"Query: '{query_content}'")
        print(f"Expected: {expected_route}, Got: {actual_route}")

        # --- Assert ---
        self.assertEqual(actual_route.strip(), expected_route)

    def test_route_to_default_another_example(self):
        """
        Test another casual question routes to DEFAULT.
        """
        print(f"\nRunning test: test_route_to_default_another_example with model {TEST_MODEL}")
        query_content = "What is the capital of France?"
        state = {
            "messages": [HumanMessage(content=query_content)]
        }
        expected_route = "DEFAULT"

        # --- Act ---
        actual_route = decide_to_route(state, model=TEST_MODEL)
        print(f"Query: '{query_content}'")
        print(f"Expected: {expected_route}, Got: {actual_route}")

        # --- Assert ---
        self.assertEqual(actual_route.strip(), expected_route)

    def test_route_borderline_simple_generation(self):
        """
        Test a borderline case that should likely be simple GENERATION.
        """
        print(f"\nRunning test: test_route_borderline_simple_generation with model {TEST_MODEL}")
        query_content = "How do I print 'Hello World' to the console in Python?"
        state = {
            "messages": [HumanMessage(content=query_content)]
        }
        # This is very simple, fitting the "simple code without external importing" description
        expected_route = "GENERATION"

        # --- Act ---
        actual_route = decide_to_route(state, model=TEST_MODEL)
        print(f"Query: '{query_content}'")
        print(f"Expected: {expected_route}, Got: {actual_route}")

        # --- Assert ---
        self.assertEqual(actual_route.strip(), expected_route)


# --- Run Tests ---

    # python -m unittest test.test_graph.test_decide_to_route
