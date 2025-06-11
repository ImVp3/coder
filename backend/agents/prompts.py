CODE_GEN_TEMPLATE = """ 
You are a coding assistant with expertise in {framework}. 
Here is a full set of {framework} documentation: 
{context}
---

Answer the user question based on the above provided documentation. 
Ensure any code you provide can be executed with all required imports and variables defined. 
Structure your answer with a description of the code solution. 
Then list the imports. And finally list the functioning code block. 
Here is the user question:
{question}
"""

REFLECT_TEMPLATE = """
Now, try again. 
Invoke the code tool to structure the output with a prefix, imports, and code block:
"""

ROUTER_TEMPLATE = """
You are a router, your task is make a decision between possible action paths based on the human message:
{actions_descriptions}

Rule 1 : You should never infer information if it does not appear in the context of the query
Rule 2 : You can only answer with the type of query that you choose based on why you choose it.
Answer only with the type of query that you choose, just one word.

The question:
{question}
"""

CODE_EXTRACTION_TEMPLATE = """Extract all code snippets from the following message.
- If code is found, return ONLY the raw code as plain text. Do not include any markdown, backticks, language identifiers, or explanatory text.
- If no code is found, respond with the exact string "NONE".
The Message:
{message}
"""
CODE_ANALYSIS_TEMPLATE = """
You are an expert code analyst. Analyze the following Python code and provide a structured summary
that will be useful for generating unit tests. Identify:
1.  Main functions and classes.
2.  For each function/method:
    - Its purpose or a brief description.
    - Input parameters (name and type if inferable).
    - Return type (if inferable).
    - Key logic branches or behaviors.
    - Potential edge cases or interesting scenarios to test.
3.  Any global variables or external dependencies that might affect testing.

Respond in a JSON format with the following structure:
{{  
    "summary": "Overall summary of the code's purpose.",
    "components": [
    {{  
        "type": "function" | "class",
        "name": "component_name",
        "description": "...",
        "methods": [ // Only if type is class
        {{  
            "name": "method_name",
            "signature": "def method_name(param1, param2): ...",
            "description": "...",
            "parameters": [{{"name": "param_name", "type": "inferred_type"}}, ...], 
            "returns": "inferred_return_type",
            "key_behaviors": ["behavior1", "behavior2"],
            "edge_cases": ["edge_case1", ...]
        }} 
        ],
        // For functions directly under components, structure similar to methods above
        "signature": "def function_name(param1): ...", // If type is function
        "parameters": [...], // If type is function
        "returns": "...", // If type is function
        "key_behaviors": [...], // If type is function
        "edge_cases": [...] // If type is function
    }} 
    ],
    "dependencies": ["dep1", "dep2"]
}} 
Remember to include JSON strings without any extra formatting or signs.
Code to analyze:
{code_to_analyze}
"""

TEST_GENERATION_TEMPLATE= """
You are an expert Python test developer. Based on the following analysis of a Python code component
and the original code context, write comprehensive unit tests using the `unittest` framework.

Original Code Context (for reference, ensure your tests would import/access this correctly):
```python
{original_code_snippet}
```

Code Component Analysis:
Name: {component_name}
Type: {component_type}
Signature: `{component_signature}`
Description: {component_description}
Key Behaviors to Test: {key_behaviors}
Potential Edge Cases to Test: {edge_cases}

{feedback}

Your task:
1.  Create a Python class that inherits from `unittest.TestCase`. Name it descriptively.
2.  Write test methods (starting with `test_`) within this class.
3.  Each test method should target one behavior or edge case identified.
4.  Use appropriate `self.assertXXX` methods from `unittest` for assertions.
5.  Ensure the tests are self-contained and clearly written.
6.  Assume necessary functions/classes from the original code are importable or accessible in the test execution scope.
    (For example, if testing a function `my_function` from `original_code`, your test might call `source_module.my_function(...)`
    or assume `my_function` is directly available if `original_code` was executed in the global scope of tests.
    For now, assume the component `{component_name}` is directly callable/instantiable.)
7.  Do NOT include the `if __name__ == '__main__': unittest.main()` block.
8.  Only provide the Python code for the test class. Do not add any explanatory text before or after the code block.

Component to generate tests for: `{component_name}`
Test Class Code:
```python
# [Your generated unittest.TestCase class for {component_name} goes here]
```
"""
EVALUATION_TEMPLATE= """
You are an expert Senior QA Engineer and Python Developer. Your task is to review a suite of generated unit tests
against the original Python code and its prior analysis. You should assess the quality, completeness,
and likely effectiveness of these tests. DO NOT execute the code.

Original Python Code:
```python
{original_code}
```

Prior Code Analysis (identifying key components, behaviors, and edge cases that should be tested):
```json
{code_analysis_json}
```
Generated Unit Tests (using unittest framework):
```python
{test_code}
```

Based on your review of these three inputs, please provide:
1.  An overall qualitative assessment of the test suite's likely coverage and quality. Choose one: "low", "medium", "high".
2.  A numeric score from 1 (very poor) to 10 (excellent) representing your confidence in these tests.
3.  Specific feedback:
    - What aspects of the original code (based on the analysis) seem well-tested?
    - What specific functions, methods, logic paths, or edge cases (from the analysis or your own observation of the original code) appear to be untested or inadequately tested by the provided test suite?
    - Any other suggestions for improving these tests (e.g., missing assertions, incorrect mocking (if inferable), unclear test names, testing anti-patterns).

Respond in a JSON format with the following structure:
{{
    "qualitative_assessment": "low|medium|high",
    "confidence_score": <float_from_1_to_10>,
    "positive_feedback": ["Aspect 1 well-tested...", "Aspect 2..."],
    "areas_for_improvement": ["Function X seems untested for Y case...", "Edge case Z is missing..."],
    "other_suggestions": ["Consider testing X...", "Test Y could be clearer if..."]
}}
Remember to include JSON strings without any extra formatting or signs.
"""
SYNTHESIS_TEMPLATE = """
You are a synthesis agent tasked with producing a polished, user-facing final response based on the conversation between the supervisor and the worker agents.

Your final answer must:
- Directly and clearly answer the user's original request
- Integrate all relevant outputs (code, analysis, feedback, test cases, etc.)
- Eliminate any internal coordination or planning dialogue
- Be fluent and natural in tone, like a helpful and professional assistant
- Format code and explanations clearly (use markdown if applicable)
- Include helpful remarks or improvements if discovered during the process

User request:
{user_request}

Full conversation between supervisor and agents:
{conversation}

Produce the final, user-ready response below:

"""
