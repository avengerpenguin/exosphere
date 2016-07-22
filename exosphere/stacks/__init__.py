from . import static_site
import importlib


def get(stack_type):
    return {
        'static_site': static_site,
    }[stack_type]
