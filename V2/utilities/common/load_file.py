import os
import json
from typing import Any

def load_json_file(filename: str, default: Any = "") -> Any:
    """
    Load the content of a text or JSON file.
    
    Args:
        filename (str): The path to the file.
        default (Any): The default value to return if the file is not found or cannot be read.

    Returns:
        Any: 
            - If the file is a JSON file, returns the parsed JSON object (dict, list, etc.)
            - If it's a text file, returns the file content as a string.
            - If the file doesn't exist or an error occurs, returns the default value.
    """
    if not os.path.isfile(filename):
        return default
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Detect by file extension
            if filename.lower().endswith('.json'):
                return json.load(file)
            else:
                return file.read()
    except Exception as e:
        print(f"⚠️ Error reading {filename}: {e}")
        return default
