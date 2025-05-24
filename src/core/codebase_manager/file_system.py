# --- file_system.py ---
import os
import shutil
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseFileSystem(ABC):
    """Abstract base class for file system operations."""
    def __init__(self, base_path: str):
        self.base_path = base_path # This is the root for this FS instance

    def _get_full_path(self, relative_path: str) -> str:
        """
        Helper to combine base_path with relative_path.
        Ensures path is normalized and kept within base_path.
        """
        # Normalize to prevent '..' from escaping the intended base_path if not handled by os.path.abspath
        # For LocalFileSystem, os.path.join already does a good job,
        # but abspath and relpath checks are still important.
        full_path = os.path.abspath(os.path.join(self.base_path, relative_path))
        if not full_path.startswith(os.path.abspath(self.base_path)):
            raise ValueError(f"Path '{relative_path}' attempts to escape base directory '{self.base_path}'")
        return full_path


    @abstractmethod
    def read_file(self, path: str) -> str:
        """Reads a file. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """Writes to a file. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a path exists. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        """Checks if a path is a directory. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """Checks if a path is a file. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def list_dir(self, path: str) -> List[str]:
        """Lists directory contents. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def create_dir(self, path: str, recursive: bool = False) -> None:
        """Creates a directory. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Deletes a file. Path is relative to self.base_path."""
        pass

    @abstractmethod
    def delete_dir(self, path: str, recursive: bool = False) -> None:
        """Deletes a directory. Path is relative to self.base_path."""
        pass


class LocalFileSystem(BaseFileSystem):
    """Implements file system operations using the local disk."""

    def read_file(self, path: str) -> str:
        full_path = self._get_full_path(path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, path: str, content: str) -> None:
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def exists(self, path: str) -> bool:
        return os.path.exists(self._get_full_path(path))

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(self._get_full_path(path))

    def is_file(self, path: str) -> bool:
        return os.path.isfile(self._get_full_path(path))

    def list_dir(self, path: str) -> List[str]:
        return os.listdir(self._get_full_path(path))

    def create_dir(self, path: str, recursive: bool = False) -> None:
        full_path = self._get_full_path(path)
        if recursive:
            os.makedirs(full_path, exist_ok=True)
        else:
            os.mkdir(full_path)

    def delete_file(self, path: str) -> None:
        full_path = self._get_full_path(path)
        os.remove(full_path)

    def delete_dir(self, path: str, recursive: bool = False) -> None:
        full_path = self._get_full_path(path)
        if recursive:
            shutil.rmtree(full_path)
        else:
            os.rmdir(full_path)

class InMemoryFileSystem(BaseFileSystem):
    """
    Implements an in-memory file system for testing or sandboxed environments.
    Paths are treated as keys in a dictionary. '/' is used as a separator.
    File content is stored as strings. Directories are implicitly defined by paths
    or explicitly by storing a special marker (e.g., a dictionary) for them.
    """
    def __init__(self, base_path: str = ""): # base_path is nominal for InMemory
        super().__init__(base_path)
        self.fs_dict: Dict[str, Any] = {"": {}} # Root directory marker, value is a dict for its content

    def _normalize_path(self, path: str) -> str:
        """Normalizes path, removing trailing slashes unless it's the root."""
        normalized = os.path.normpath(path).replace("\\", "/")
        if normalized == ".":
            return "" # Represent root as empty string internally
        if normalized.startswith("/"): # os.normpath might return /foo for foo
            normalized = normalized[1:]
        return normalized

    def _get_parent_path(self, path: str) -> str:
        parent = os.path.dirname(path).replace("\\", "/")
        if parent == path: # root's parent is root
            return ""
        return self._normalize_path(parent)

    def _get_node(self, path: str) -> Optional[Any]:
        """Traverses the fs_dict to find the node (file or directory dict) at the given path."""
        current_level = self.fs_dict[""] # Start at root's content dict
        if not path: # Path is root
            return current_level

        parts = path.split('/')
        for i, part in enumerate(parts):
            if not isinstance(current_level, dict) or part not in current_level:
                return None
            current_level = current_level[part]
        return current_level

    def _ensure_parent_dir_exists(self, path: str):
        """Ensures all parent directories for a given path exist."""
        parent_path = self._get_parent_path(path)
        parts = parent_path.split('/') if parent_path else []
        current_level = self.fs_dict[""] # Root content
        current_path_trace = ""
        for part in parts:
            if part not in current_level or not isinstance(current_level[part], dict):
                current_level[part] = {} # Create directory
            current_level = current_level[part]
            current_path_trace = os.path.join(current_path_trace, part)


    def read_file(self, path: str) -> str:
        n_path = self._normalize_path(path)
        node = self._get_node(n_path)
        if isinstance(node, str):
            return node
        raise FileNotFoundError(f"File not found or '{path}' is a directory.")


    def write_file(self, path: str, content: str) -> None:
        n_path = self._normalize_path(path)
        if not n_path:
            raise ValueError("Cannot write to root path directly as a file.")
        self._ensure_parent_dir_exists(n_path)

        parent_path = self._get_parent_path(n_path)
        file_name = os.path.basename(n_path)

        parent_node_content = self._get_node(parent_path)
        if not isinstance(parent_node_content, dict):
            # This should not happen if _ensure_parent_dir_exists works correctly
            raise NotADirectoryError(f"Parent path '{parent_path}' is not a directory.")

        parent_node_content[file_name] = content


    def exists(self, path: str) -> bool:
        n_path = self._normalize_path(path)
        return self._get_node(n_path) is not None

    def is_dir(self, path: str) -> bool:
        n_path = self._normalize_path(path)
        node = self._get_node(n_path)
        return isinstance(node, dict)

    def is_file(self, path: str) -> bool:
        n_path = self._normalize_path(path)
        node = self._get_node(n_path)
        return isinstance(node, str)

    def list_dir(self, path: str) -> List[str]:
        n_path = self._normalize_path(path)
        node = self._get_node(n_path)
        if isinstance(node, dict):
            return list(node.keys())
        raise NotADirectoryError(f"Path '{path}' is not a directory or does not exist.")

    def create_dir(self, path: str, recursive: bool = False) -> None:
        n_path = self._normalize_path(path)
        if self.exists(n_path):
            if self.is_dir(n_path):
                return # Already exists
            else:
                raise FileExistsError(f"Path '{path}' exists and is a file.")

        if recursive:
            self._ensure_parent_dir_exists(n_path) # Create parents
            # Now create the final directory itself
            parts = n_path.split('/')
            current_level = self.fs_dict[""]
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                elif not isinstance(current_level[part], dict):
                    raise FileExistsError(f"A file exists at part '{part}' of path '{path}'")
                current_level = current_level[part]
        else:
            parent_path = self._get_parent_path(n_path)
            if not self.is_dir(parent_path):
                raise FileNotFoundError(f"Parent directory for '{path}' does not exist.")
            file_name = os.path.basename(n_path)
            parent_node_content = self._get_node(parent_path)
            if isinstance(parent_node_content, dict): # Should be true due to is_dir check
                parent_node_content[file_name] = {}
            else:
                # Should not be reached if logic is correct
                raise NotADirectoryError(f"Parent path '{parent_path}' is not a directory despite check.")


    def delete_file(self, path: str) -> None:
        n_path = self._normalize_path(path)
        if not self.is_file(n_path):
            raise FileNotFoundError(f"File '{path}' not found or is a directory.")

        parent_path = self._get_parent_path(n_path)
        file_name = os.path.basename(n_path)
        parent_node_content = self._get_node(parent_path)
        if isinstance(parent_node_content, dict) and file_name in parent_node_content:
            del parent_node_content[file_name]
        else:
            # Should ideally not be reached if is_file passed
            raise FileNotFoundError(f"File '{path}' could not be deleted (inconsistency).")


    def delete_dir(self, path: str, recursive: bool = False) -> None:
        n_path = self._normalize_path(path)
        if not self.is_dir(n_path):
            raise NotADirectoryError(f"Directory '{path}' not found or is a file.")

        dir_content = self._get_node(n_path)
        if isinstance(dir_content, dict) and dir_content and not recursive:
            raise OSError(f"Directory '{path}' is not empty.")

        parent_path = self._get_parent_path(n_path)
        dir_name = os.path.basename(n_path)
        if not dir_name and n_path == "": # Cannot delete root
            raise ValueError("Cannot delete the root directory.")

        parent_node_content = self._get_node(parent_path)
        if isinstance(parent_node_content, dict) and dir_name in parent_node_content:
            del parent_node_content[dir_name]
        else:
            # Should ideally not be reached
            raise NotADirectoryError(f"Directory '{path}' could not be deleted (inconsistency).")
