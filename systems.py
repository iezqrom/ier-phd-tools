import platform
import os
import importlib.util
import sys
import datetime


def grab_system_info():
    """
    Collects and returns the node (hostname) of the system.
    
    Returns:
        str: The node (hostname) of the system.
    """
    system_info = platform.uname()
    return system_info.node


def find_parent_folder(marker_file, start_dir=None):
    """
    Finds the parent folder containing the specified marker file, starting from the given directory.

    Parameters:
        marker_file (str): The name of the marker file to search for.
        start_dir (str, optional): The directory to start searching from. Defaults to the current working directory.

    Returns:
        str: The path to the parent folder containing the marker file, or None if not found.
    """
    if start_dir is None:
        start_dir = os.getcwd()
        
    current_dir = os.path.abspath(start_dir)
    while current_dir != os.path.dirname(current_dir):
        current_dir = current_dir.replace('//', '/')
        if os.path.exists(os.path.join(current_dir, marker_file)):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None


def import_module(file_path, module_file_name):
    """
    Imports a module from the specified file path.

    Parameters:
        file_path (str): The path to the directory containing the module file.
        module_file_name (str): The name of the module file.

    Returns:
        module: The imported module.
    """
    module_name = module_file_name.split('.')[0]
    file_path = os.path.join(file_path, module_file_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def define_folder_name(name):
    """
    Defines a folder name by ensuring it only contains letters, numbers, and hyphens, 
    replacing invalid characters with hyphens, and appending the current date.

    Parameters:
        name (str): The base name for the folder.

    Returns:
        str: The formatted folder name.
    """
    name = str(name)
    name = ''.join(e if e.isalnum() or e == '_' else '_' for e in name)
    date = datetime.datetime.now().strftime("%y%m%d")
    return f"{name}_{date}"
