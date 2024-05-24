import platform
import os
import importlib.util
import sys
import datetime

def grabSystemInfo():
    # Collect system information
    system_info = platform.uname()

    return system_info.node

def findParentFolder(marker_file, start_dir=None):
    if start_dir is None:
        start_dir = os.getcwd()
        
    current_dir = os.path.abspath(start_dir)
    while current_dir != os.path.dirname(current_dir):
        current_dir = current_dir.replace('//', '/')
        if os.path.exists(os.path.join(current_dir, marker_file)):
            print(current_dir)
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None

def importModule(file_path, module_file_name):
    module_name = module_file_name.split('.')[0]
    file_path = file_path + '/' + module_file_name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def defineFolderName(name):
    # ensure the name is a string
    name = str(name)
    # ensure that it only contains letter, numbers and -. characters that are not letters, numbers of - are replaced by -
    name = ''.join(e if e.isalnum() or e == '-' else '-' for e in name)
    date = datetime.datetime.now().strftime("%y%m%d")
    return f"{name}_{date}"

