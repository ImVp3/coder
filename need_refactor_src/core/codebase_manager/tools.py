

# --- tools.py ---
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any, Optional

from .core import CodebaseManager
from .exceptions import FileNotFoundException, OperationNotPermittedException


class BaseCodebaseTool(BaseModel):
    """Base model for shared CodebaseManager instance."""
    cb_manager: CodebaseManager = Field(exclude=True) # Exclude from schema, passed at runtime

    class Config:
        arbitrary_types_allowed = True


class ReadFileSchema(BaseModel):
    """Input schema for ReadFileTool."""
    file_path: str = Field(description="The relative path to the file from the codebase root.")

class ReadFileTool(BaseTool, BaseCodebaseTool):
    """Tool to read the content of a file within the codebase."""
    name: str = "read_codebase_file"
    description: str = (
        "Reads the content of a specified file within the managed codebase. "
        "Use this to get the source code of a file."
    )
    args_schema: Type[BaseModel] = ReadFileSchema

    def _run(self, file_path: str) -> str:
        """Use the tool."""
        try:
            return self.cb_manager.read_file(file_path)
        except FileNotFoundException as e:
            return f"Error: File not found at path '{file_path}'."
        except Exception as e:
            return f"An unexpected error occurred while reading '{file_path}': {str(e)}"


class WriteFileSchema(BaseModel):
    """Input schema for WriteFileTool."""
    file_path: str = Field(description="The relative path to the file from the codebase root.")
    content: str = Field(description="The new content to write to the file.")
    overwrite: bool = Field(default=True, description="Whether to overwrite the file if it exists.")

class WriteFileTool(BaseTool, BaseCodebaseTool):
    """Tool to write content to a file within the codebase."""
    name: str = "write_codebase_file"
    description: str = (
        "Writes (or overwrites) content to a specified file within the managed codebase. "
        "Parent directories will be created if they don't exist. "
        "Use this to create new code files or modify existing ones."
    )
    args_schema: Type[BaseModel] = WriteFileSchema

    def _run(self, file_path: str, content: str, overwrite: bool = True) -> str:
        """Use the tool."""
        try:
            self.cb_manager.write_file(file_path, content, overwrite=overwrite)
            return f"Successfully wrote to file: '{file_path}'"
        except OperationNotPermittedException as e:
            return f"Error: Operation not permitted. {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred while writing to '{file_path}': {str(e)}"


class ListDirectorySchema(BaseModel):
    """Input schema for ListDirectoryTool."""
    dir_path: str = Field(default=".", description="The relative path to the directory from the codebase root. Defaults to the root.")

class ListDirectoryTool(BaseTool, BaseCodebaseTool):
    """Tool to list the contents of a directory within the codebase."""
    name: str = "list_codebase_directory"
    description: str = (
        "Lists the files and subdirectories within a specified directory of the managed codebase. "
        "Use '.' for the root directory. Useful for exploring the codebase structure."
    )
    args_schema: Type[BaseModel] = ListDirectorySchema

    def _run(self, dir_path: str = ".") -> List[str] | str:
        """Use the tool."""
        try:
            return self.cb_manager.list_directory(dir_path)
        except FileNotFoundException:
            return f"Error: Directory not found at path '{dir_path}'."
        except Exception as e:
            return f"An unexpected error occurred while listing directory '{dir_path}': {str(e)}"

class GetFileStructureSchema(BaseModel):
    """Input schema for GetFileStructureTool."""
    file_path: str = Field(description="The relative path to the Python file from the codebase root.")

class GetFileStructureTool(BaseTool, BaseCodebaseTool):
    """Tool to get the structure (functions, classes) of a Python file."""
    name: str = "get_python_file_structure"
    description: str = (
        "Retrieves the structure of a Python file, including functions, classes, methods, "
        "and their signatures and docstrings. Only works for .py files. "
        "Useful for understanding the organization of a specific code file."
    )
    args_schema: Type[BaseModel] = GetFileStructureSchema

    def _run(self, file_path: str) -> Dict[str, Any] | str:
        """Use the tool."""
        try:
            structure = self.cb_manager.get_file_structure(file_path)
            if structure is None and file_path.endswith(".py"):
                return f"Could not parse structure for Python file: '{file_path}'. It might be empty or have syntax errors."
            elif structure is None:
                return f"Error: '{file_path}' is not a Python file or could not be accessed."
            return structure
        except FileNotFoundException:
            return f"Error: File not found at path '{file_path}'."
        except Exception as e:
            return f"An unexpected error occurred while getting structure of '{file_path}': {str(e)}"


class GetFullCodebaseStructureSchema(BaseModel):
    """Input schema for GetFullCodebaseStructureTool."""
    ignored_dirs: Optional[List[str]] = Field(
        default=None,
        description="A list of directory names to ignore (e.g., ['.git', '__pycache__'])."
    )

class GetFullCodebaseStructureTool(BaseTool, BaseCodebaseTool):
    """Tool to get the structure of all Python files in the entire codebase."""
    name: str = "get_full_codebase_structure"
    description: str = (
        "Recursively scans the entire codebase and returns a dictionary where keys are "
        "relative file paths of Python files, and values are their parsed structures "
        "(functions, classes, methods, docstrings). "
        "Useful for getting a global overview of the codebase components. "
        "Can specify directories to ignore."
    )
    args_schema: Type[BaseModel] = GetFullCodebaseStructureSchema

    def _run(self, ignored_dirs: Optional[List[str]] = None) -> Dict[str, Any] | str:
        """Use the tool."""
        try:
            return self.cb_manager.get_full_codebase_structure(ignored_dirs=ignored_dirs)
        except Exception as e:
            return f"An unexpected error occurred while getting the full codebase structure: {str(e)}"
