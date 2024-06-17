import os
from setuptools import Extension, setup

NO_EXTENSIONS = os.getenv("NO_EXTENSIONS", "FALSE").lower() == "true"

try:
    from Cython.Build import cythonize
except ImportError:
    NO_EXTENSIONS = True

setup(
    name="python-ottype",
    ext_modules=(
        cythonize([Extension("ottype.core_boost", ["ottype/core_boost.pyx"])])
        if not NO_EXTENSIONS
        else []
    ),
)
