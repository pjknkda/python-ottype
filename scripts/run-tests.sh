#!/bin/bash
set -e -x

TARGET_PYBIN=("cp38-cp38" "cp39-cp39" "cp310-cp310" "cp311-cp311")
cd /io

# Install packages and test
for PYBIN in "${TARGET_PYBIN[@]}"; do
    /opt/python/${PYBIN}/bin/python -m venv /tmp/py-venv-${PYBIN}

    source /tmp/py-venv-${PYBIN}/bin/activate
    python -m pip install --no-cache-dir -e .[dev]
    python setup.py build_ext --inplace
    python -m pytest -v .
    deactivate
done
