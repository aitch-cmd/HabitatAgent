import os

def load_instructions_file(filename:str, default: str=""):
    """
    Load the content of a text file as a string.
    
    Args:
        filename (str): The path to the text file.
        default (str): The default content to return if the file is not found.

    Returns:
        str: The content of the file or the default content if the file is not found.
    """
    if not os.path.isfile(filename):
        return default
    
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    return default