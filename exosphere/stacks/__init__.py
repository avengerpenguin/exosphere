from . import static_site
import importlib

def get(stack_type):
    return importlib.import_module(stack_type, '.')
