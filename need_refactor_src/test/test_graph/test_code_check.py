# SUPER IMPORTANT NOTE: these testcases were created by Gemini. I was too lazy to check carefully XD

import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ---
import unittest
from typing import Dict, Any, List, Optional
import ast
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.documents import Document


from core.utils.schema import Code
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) # Adjust depth as needed
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from core.graph.utils.codegen_nodes.code_check import (
    static_syntax_check_v2,
    NODE_NAME, # Import NODE_NAME if used in constants
    FLOW_PASSED,
    FLOW_FAILED_SYNTAX,
    FLOW_FAILED_UNEXPECTED,
    FLOW_NO_GENERATION,
    FLOW_INVALID_FORMAT,
    FLOW_EMPTY_CODE,
    MESSAGE_NO_GENERATION,
    MESSAGE_INVALID_FORMAT,
    MESSAGE_EMPTY_CODE
)


# --- Test Class ---

class TestStaticSyntaxCheckV2(unittest.TestCase):

    def _create_base_state(
        self,
        messages: Optional[List[BaseMessage]] = None,
        generation: Optional[List[Any]] = None, # Allow Any for invalid format tests
        iterations: int = 1,
        documentation: Optional[List[Document]] = None,
        flow: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Helper to create a default state dictionary."""
        return {
            "messages": messages if messages is not None else [HumanMessage(content="Initial prompt")],
            "generation": generation if generation is not None else [],
            "iterations": iterations,
            "documentation": documentation if documentation is not None else [Document(page_content="Some docs")],
            "flow": flow if flow is not None else ["Start", "Generate"],
            "error": False # Initial error state is usually False before check
        }

    def test_valid_syntax(self):
        """Test case with syntactically correct code."""
        valid_code = Code(prefix="Valid code", imports="import os", code="print(os.name)")
        state = self._create_base_state(generation=[valid_code])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow']) # Copy

        result = static_syntax_check_v2(state)

        self.assertFalse(result['error'], "Error flag should be False for valid syntax")
        self.assertEqual(len(result['messages']), initial_messages_count, "No error message should be added")
        # Check the specific flow message constant
        self.assertIn("Static Syntax Check: Passed", result['flow'][-1], "Flow should indicate Passed") # Check substring in case constant isn't imported
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")
        # Check pass-through fields
        self.assertEqual(result['iterations'], state['iterations'])
        self.assertEqual(result['documentation'], state['documentation'])
        self.assertEqual(result['generation'], state['generation']) # Ensure generation list is passed through


    def test_syntax_error(self):
        """Test case with a clear syntax error."""
        invalid_code = Code(prefix="Invalid code", imports="import sys", code="print(sys.version\n") # Missing closing parenthesis
        state = self._create_base_state(generation=[invalid_code])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True for syntax error")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], HumanMessage, "Error message should be HumanMessage for LLM")
        self.assertIn("syntax error (static check)", result['messages'][-1].content)
        # Line number depends on combined code. imports=1 line, code starts line 2. Error is line 1 of code block -> line 2 overall
        self.assertIn("Line: 2", result['messages'][-1].content) # AST parse counts from combined string
        self.assertIn("print(sys.version", result['messages'][-1].content) # Check snippet
        # Check the specific flow message constant
        self.assertIn("Static Syntax Check: Failed", result['flow'][-1], "Flow should indicate SyntaxError") # Check substring
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")

    def test_syntax_error_in_imports(self):
        """Test case with a syntax error in the imports."""
        invalid_code = Code(prefix="Invalid import", imports="import sys\nimport os.", code="print('hello')") # Invalid import syntax
        state = self._create_base_state(generation=[invalid_code])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True for syntax error in imports")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], HumanMessage, "Error message should be HumanMessage")
        self.assertIn("syntax error (static check)", result['messages'][-1].content)
        self.assertIn("Line: 2", result['messages'][-1].content) # Error is on the second line of the combined code
        self.assertIn("import os.", result['messages'][-1].content) # Check snippet
        self.assertIn("Static Syntax Check: Failed", result['flow'][-1], "Flow should indicate SyntaxError")
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")


    def test_no_generation(self):
        """Test case where the 'generation' list is empty."""
        state = self._create_base_state(generation=[])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True when no generation exists")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], SystemMessage, "Error message should be SystemMessage")
        self.assertEqual(result['messages'][-1].content, MESSAGE_NO_GENERATION)
        self.assertEqual(result['flow'][-1], FLOW_NO_GENERATION, "Flow should indicate No Generation")
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")

    def test_invalid_generation_format_dict(self):
        """Test case where the last generation item is an invalid dictionary."""
        # This dict cannot be validated into a Code object by pydantic
        invalid_gen = {"wrong_key": "import os", "code_content": "print('hello')"}
        state = self._create_base_state(generation=[invalid_gen])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True for invalid format (dict)")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], SystemMessage, "Error message should be SystemMessage")
        self.assertEqual(result['messages'][-1].content, MESSAGE_INVALID_FORMAT)
        self.assertEqual(result['flow'][-1], FLOW_INVALID_FORMAT, "Flow should indicate Invalid Format")
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")

    def test_invalid_generation_format_other_type(self):
        """Test case where the last generation item is not a Code object or dict."""
        invalid_gen = "just a string"
        state = self._create_base_state(generation=[invalid_gen])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True for invalid format (string)")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], SystemMessage, "Error message should be SystemMessage")
        self.assertEqual(result['messages'][-1].content, MESSAGE_INVALID_FORMAT)
        self.assertEqual(result['flow'][-1], FLOW_INVALID_FORMAT, "Flow should indicate Invalid Format")
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")

    def test_empty_code_and_imports(self):
        """Test case where the Code object has empty imports and code."""
        empty_code = Code(prefix="Empty code", imports="", code="")
        state = self._create_base_state(generation=[empty_code])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        self.assertTrue(result['error'], "Error flag should be True for empty code/imports")
        self.assertEqual(len(result['messages']), initial_messages_count + 1, "One error message should be added")
        self.assertIsInstance(result['messages'][-1], SystemMessage, "Error message should be SystemMessage")
        self.assertEqual(result['messages'][-1].content, MESSAGE_EMPTY_CODE)
        self.assertEqual(result['flow'][-1], FLOW_EMPTY_CODE, "Flow should indicate Empty Code/Imports")
        self.assertEqual(result['flow'][:-1], initial_flow, "Original flow should be preserved")

    def test_valid_code_with_existing_messages_and_flow(self):
        """Test valid syntax check preserves existing state elements."""
        initial_msgs = [
            HumanMessage(content="Start"),
            SystemMessage(content="System info")
        ]
        initial_flow_entries = ["Start", "Generate", "SomeOtherStep"]
        valid_code = Code(prefix="Valid", imports="import math", code="print(math.pi)")
        state = self._create_base_state(
            messages=list(initial_msgs), # Pass copies
            generation=[valid_code],
            flow=list(initial_flow_entries)
        )

        result = static_syntax_check_v2(state)

        self.assertFalse(result['error'])
        self.assertEqual(len(result['messages']), len(initial_msgs)) # No message added
        self.assertEqual(result['messages'], initial_msgs) # Original messages preserved
        self.assertIn("Static Syntax Check: Passed", result['flow'][-1]) # Check substring
        self.assertEqual(result['flow'][:-1], initial_flow_entries) # Original flow preserved

    def test_multiple_generations_checks_last(self):
        """Test that only the last generation in the list is checked."""
        invalid_code_old = Code(prefix="Invalid old", imports="", code="print(")
        valid_code_new = Code(prefix="Valid new", imports="import os", code="print(os.getcwd())")
        state = self._create_base_state(generation=[invalid_code_old, valid_code_new])
        initial_messages_count = len(state['messages'])
        initial_flow = list(state['flow'])

        result = static_syntax_check_v2(state)

        # Should pass because the *last* generation is valid
        self.assertFalse(result['error'], "Error flag should be False as the last generation is valid")
        self.assertEqual(len(result['messages']), initial_messages_count, "No error message should be added")
        self.assertIn("Static Syntax Check: Passed", result['flow'][-1])
        self.assertEqual(result['flow'][:-1], initial_flow)
        self.assertEqual(result['generation'], state['generation'], "Generation list should be passed through unchanged")

    # Note: Testing the FLOW_FAILED_UNEXPECTED case directly is hard without
    # mocking ast.parse to raise a non-SyntaxError, which adds complexity.
    # We trust that the except Exception block works as intended.

# --- Run Tests ---
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # Added argv for compatibility with some environments
