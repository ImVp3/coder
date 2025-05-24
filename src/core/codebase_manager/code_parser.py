import ast
from typing import List, Dict, Any, Tuple

class PythonCodeParser:
    """
    Parses Python code to extract structural information like functions, classes, and their signatures.
    """
    def parse_structure(self, code_content: str) -> Dict[str, Any]:
        """
        Parses Python code content and extracts functions and classes.
        Args:
            code_content (str): The Python code as a string.
        Returns:
            Dict[str, Any]: A dictionary with 'functions' and 'classes' lists.
                            Each item contains name, signature, and docstring.
        """
        tree = ast.parse(code_content)
        structure = {"functions": [], "classes": []}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, code_content)
                # Check if it's a method (i.e., defined within a class)
                is_method = any(isinstance(parent, ast.ClassDef) for parent in self._get_node_parents(tree, node))
                if not is_method:
                    structure["functions"].append(func_info)

            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": [],
                    "attributes": [] # Could be extended with ast.Assign nodes within class
                }
                for item in node.body:
                    if isinstance(item, ast.FunctionDef): # Method
                        class_info["methods"].append(self._extract_function_info(item, code_content))
                    elif isinstance(item, ast.Assign): # Class or instance variable
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info["attributes"].append({"name": target.id, "value_type": "variable"})
                            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                class_info["attributes"].append({"name": target.attr, "value_type": "instance_variable"})


                structure["classes"].append(class_info)
        return structure

    def _extract_function_info(self, node: ast.FunctionDef, code_content: str) -> Dict[str, Any]:
        """Helper to extract information from an ast.FunctionDef node."""
        signature = self._reconstruct_signature(node, code_content)
        return {
            "name": node.name,
            "signature": signature,
            "docstring": ast.get_docstring(node) or "",
            "lineno_start": node.lineno,
            "lineno_end": node.end_lineno
        }

    def _reconstruct_signature(self, node: ast.FunctionDef, code_content: str) -> str:
        """
        Tries to reconstruct the function signature string including decorators.
        This is a simplified reconstruction.
        """
        lines = code_content.splitlines()
        start_line = node.lineno -1
        end_line = node.body[0].lineno -1 if node.body else start_line # up to the line before the body starts

        # Include decorators
        decorator_list = node.decorator_list
        first_deco_lineno = decorator_list[0].lineno if decorator_list else node.lineno
        start_line = min(start_line, first_deco_lineno -1)


        # Find the end of the signature (before the colon and potential type hint for return)
        sig_end_line = node.lineno -1 # line of 'def foo(...):'
        for i in range(start_line, len(lines)):
            if lines[i].rstrip().endswith(":"):
                sig_end_line = i
                break
        # If there is a return type hint on the next line due to black formatting
        if sig_end_line + 1 < len(lines) and node.returns and hasattr(node.returns, 'lineno') and node.returns.lineno > node.lineno:
             if lines[sig_end_line].rstrip().endswith("->") and lines[sig_end_line+1].lstrip().startswith(ast.unparse(node.returns).strip()):
                 sig_end_line +=1


        full_signature_lines = lines[start_line : sig_end_line + 1]
        return "\n".join(line.strip() for line in full_signature_lines if line.strip())


    def _get_node_parents(self, tree: ast.AST, node: ast.AST) -> List[ast.AST]:
        """Helper to find parent nodes of a given node in the AST."""
        parents = []
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                if child is node:
                    parents.append(parent)
        return parents
