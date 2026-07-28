import os
import importlib
from styles.base_style import BaseStyle

def load_styles():
    styles = {}
    styles_dir = os.path.dirname(__file__)

    for filename in os.listdir(styles_dir):
        if filename.endswith(".py") and filename not in ("__init__.py", "base_style.py"):
            module_name = f"styles.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseStyle) and attr is not BaseStyle:
                        styles[attr.name.lower()] = attr()
            except Exception:
                pass

    return styles