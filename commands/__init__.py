import pkgutil
import importlib

def import_submodules(package_name):
    package = importlib.import_module(package_name)
    package_path = package.__path__
    for _, modname, ispkg in pkgutil.walk_packages(package_path, package_name + "."):
        if not ispkg:
            importlib.import_module(modname)

import_submodules(__name__)