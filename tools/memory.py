import os
from typing import Optional

def manage_memory(mode: str, content: Optional[str] = None, filepath: str = "memory.md") -> Optional[str]:
    """
    Manage a markdown memory file with read, write, and append operations.
    
    Args:
        mode (str): Operation mode - 'r' (read), 'w' (write), 'a' (append)
        content (str, optional): Content to write or append. Required for 'w' and 'a' modes
        filepath (str): Path to the memory file. Defaults to "memory.md"
    
    Returns:
        str: File content for read mode, success message for write/append modes
        None: If operation fails
    
    Examples:
        # Read memory
        memory = manage_memory('r')
        
        # Write new memory (overwrites existing)
        manage_memory('w', "# My Memory\n\nImportant notes here")
        
        # Append to memory
        manage_memory('a', "\n\n## New Section\n\nAdditional information")
    """
    
    try:
        if mode == 'r':
            # Read mode
            if not os.path.exists(filepath):
                return "Memory file does not exist yet."
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif mode == 'w':
            # Write mode (overwrite)
            if content is None:
                raise ValueError("Content is required for write mode")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote to {filepath}"
        
        elif mode == 'a':
            # Append mode
            if content is None:
                raise ValueError("Content is required for append mode")
            
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully appended to {filepath}"
        
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'r', 'w', or 'a'")
    
    except Exception as e:
        return f"Error: {str(e)}"


