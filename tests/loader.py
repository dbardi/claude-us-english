"""Load the hyphenated source file as an importable module.

`us-english.py` is not a valid Python identifier, so it cannot be imported
normally. Keeping the source filename identical to the installed filename means
installation is a plain copy with no rename step to get wrong, which is worth
this small amount of loader machinery.
"""
import importlib.util
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"


def load(filename):
    path = SRC / filename
    spec = importlib.util.spec_from_file_location(
        path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
