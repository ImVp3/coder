# --- core.py ---
import os
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field

from .file_system import BaseFileSystem, LocalFileSystem
from .code_parser import PythonCodeParser
from .exceptions import FileNotFoundException, OperationNotPermittedException

class CodebaseManager:
    """
    Manages a codebase, providing an interface for AI agents to read,
    write, and understand code files within a specified root directory.
    """
    def __init__(self, root_path: str, fs_impl: Type[BaseFileSystem] = LocalFileSystem):
        """
        Initializes the CodebaseManager.

        Args:
            root_path (str): The root directory of the codebase to manage.
            fs_impl (Type[BaseFileSystem]): The file system implementation to use.
                                            Defaults to LocalFileSystem.
        """
        self.root_path = os.path.abspath(root_path)
        self.fs: BaseFileSystem = fs_impl(base_path=self.root_path)
        self.parser = PythonCodeParser() # Can be extended for other languages

        if not self.fs.exists("."): # Check if root path is accessible via fs impl
            # This check depends on how fs.exists is implemented relative to its base_path
            # For LocalFileSystem, self.fs.exists("") or self.fs.exists(".") might be appropriate
            # to check if the root_path itself is valid.
            # Or simply try an operation like self.fs.list_dir("")
            try:
                self.fs.list_dir("") # Try a benign operation to ensure root is valid
            except Exception as e:
                raise OperationNotPermittedException(
                    f"Root path '{self.root_path}' is not accessible or does not exist. Error: {e}"
                )
        print(f"CodebaseManager initialized at: {self.root_path}")


    def _resolve_path(self, relative_path: str) -> str:
        """
        Resolves a relative path against the root_path and normalizes it.
        Ensures the path stays within the root directory for security.

        Args:
            relative_path (str): The relative path from the codebase root.

        Returns:
            str: The absolute, normalized path.

        Raises:
            OperationNotPermittedException: If the path attempts to go outside the root directory.
        """
        # This internal method is crucial for security when using LocalFileSystem directly
        # For a pure VFS, the VFS implementation itself would handle this.
        # With LocalFileSystem, we need to be careful.
        if isinstance(self.fs, LocalFileSystem): # Only do this specific check for LocalFileSystem
            full_path = os.path.abspath(os.path.join(self.root_path, relative_path))
            if not full_path.startswith(self.root_path):
                raise OperationNotPermittedException(
                    f"Attempted to access path '{relative_path}' outside of the root directory '{self.root_path}'"
                )
            return os.path.relpath(full_path, self.root_path) # Return path relative to root for fs ops
        return relative_path # For other VFS, they handle paths internally

    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a file within the codebase.

        Args:
            file_path (str): The relative path to the file from the codebase root.

        Returns:
            str: The content of the file.

        Raises:
            FileNotFoundException: If the file does not exist.
        """
        resolved_path = self._resolve_path(file_path)
        if not self.fs.is_file(resolved_path):
            raise FileNotFoundException(f"File not found: {file_path} (resolved: {resolved_path})")
        return self.fs.read_file(resolved_path)

    def write_file(self, file_path: str, content: str, overwrite: bool = True) -> None:
        """
        Writes content to a file within the codebase. Creates parent directories if they don't exist.

        Args:
            file_path (str): The relative path to the file from the codebase root.
            content (str): The content to write to the file.
            overwrite (bool): Whether to overwrite the file if it already exists.
                              If False and file exists, raises OperationNotPermittedException.
        """
        resolved_path = self._resolve_path(file_path)
        if not overwrite and self.fs.exists(resolved_path):
            raise OperationNotPermittedException(
                f"File '{file_path}' already exists and overwrite is set to False."
            )
        # Ensure parent directories exist
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir and not self.fs.exists(parent_dir):
            self.fs.create_dir(parent_dir, recursive=True)

        self.fs.write_file(resolved_path, content)
        print(f"File written: {resolved_path}")

    def list_directory(self, dir_path: str = ".") -> List[str]:
        """
        Lists the contents of a directory within the codebase.

        Args:
            dir_path (str): The relative path to the directory from the codebase root.
                            Defaults to the root directory.

        Returns:
            List[str]: A list of names of files and subdirectories.

        Raises:
            FileNotFoundException: If the directory does not exist.
        """
        resolved_path = self._resolve_path(dir_path)
        if not self.fs.is_dir(resolved_path):
            raise FileNotFoundException(f"Directory not found: {dir_path}")
        return self.fs.list_dir(resolved_path)

    def get_file_structure(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the structure of a Python file (functions, classes).

        Args:
            file_path (str): The relative path to the Python file.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the file structure
                                      (e.g., {'functions': [...], 'classes': [...]})
                                      or None if the file is not a Python file or cannot be parsed.
        """
        if not file_path.endswith(".py"):
            print(f"Warning: '{file_path}' is not a Python file. Skipping structure parsing.")
            return None
        try:
            content = self.read_file(file_path)
            return self.parser.parse_structure(content)
        except FileNotFoundException:
            raise
        except Exception as e:
            print(f"Error parsing structure of '{file_path}': {e}")
            return None

    def get_full_codebase_structure(self, ignored_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Recursively gets the structure of all Python files in the codebase.

        Args:
            ignored_dirs (Optional[List[str]]): A list of directory names to ignore (e.g., ['.git', '__pycache__']).

        Returns:
            Dict[str, Any]: A dictionary where keys are relative file paths and
                            values are their parsed structures.
        """
        if ignored_dirs is None:
            ignored_dirs = ['.git', '__pycache__', '.venv', 'node_modules', 'build', 'dist']

        codebase_structure = {}
        items_to_scan = [""] # Start with the root directory relative path

        scanned_paths = set()

        while items_to_scan:
            current_relative_dir = items_to_scan.pop(0)
            if current_relative_dir in scanned_paths:
                continue
            scanned_paths.add(current_relative_dir)

            try:
                # Ensure we don't try to list_dir on a path that is actually a file pushed into items_to_scan
                # This check might be redundant if list_dir itself handles this or if _resolve_path is robust.
                # However, adding a direct is_dir check before listing can prevent errors.
                resolved_current_dir = self._resolve_path(current_relative_dir)
                if not self.fs.is_dir(resolved_current_dir):
                    continue # Skip if it's not a directory

                for item_name in self.fs.list_dir(resolved_current_dir):
                    # Construct the relative path from the root of the codebase
                    relative_item_path = os.path.join(current_relative_dir, item_name)
                    resolved_item_path = self._resolve_path(relative_item_path) # Path for fs operations

                    if self.fs.is_dir(resolved_item_path):
                        if item_name not in ignored_dirs:
                            items_to_scan.append(relative_item_path) # Add dir for further scanning
                    elif self.fs.is_file(resolved_item_path) and item_name.endswith(".py"):
                        structure = self.get_file_structure(relative_item_path)
                        if structure:
                            codebase_structure[relative_item_path] = structure
            except FileNotFoundException:
                # This can happen if a directory is deleted during the scan.
                print(f"Warning: Directory '{current_relative_dir}' not found during scan.")
            except Exception as e:
                print(f"Error scanning directory '{current_relative_dir}': {e}")
        return codebase_structure

    # More methods: create_directory, delete_file, delete_directory, search_code, etc.


