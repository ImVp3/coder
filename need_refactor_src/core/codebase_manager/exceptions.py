

# --- exceptions.py ---
class CodebaseManagerException(Exception):
    """Base exception for the codebase manager."""
    pass

class FileNotFoundException(CodebaseManagerException):
    """Raised when a file or directory is not found."""
    pass

class OperationNotPermittedException(CodebaseManagerException):
    """Raised when an operation is not permitted (e.g., overwrite disabled, access outside root)."""
    pass