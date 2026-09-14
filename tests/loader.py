"""Load the hyphenated source files as importable modules.

`us-english.py` is not a valid Python identifier, so it cannot be imported
normally. Keeping the source filename identical to the installed filename means
installation is a plain copy with no rename step to get wrong, which is worth
this small amount of loader machinery.

Files are named by their path from the repository root, so a tool that is not
installed loads the same way as the script that is.
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(
        path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
