#!/bin/bash
set -e -x

TARGET_PYBIN=("cp39-cp39" "cp310-cp310" "cp311-cp311" "cp312-cp312" "pp39-pypy39_pp73" "pp310-pypy310_pp73")
cd /io

# Install packages and test
for PYBIN in "${TARGET_PYBIN[@]}"; do
    /opt/python/${PYBIN}/bin/python -m venv /tmp/py-venv-${PYBIN}

    source /tmp/py-venv-${PYBIN}/bin/activate
    python -m pip install --no-cache-dir .[dev]
    python -m pip install --no-cache-dir build setuptools wheel
    python -m build
    make build_inplace
    python -m pytest -v .
    deactivate
done
