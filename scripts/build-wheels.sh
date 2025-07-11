#!/bin/bash
set -e -x

TARGET_PYBIN=(
    "cp39-cp39"
    "cp310-cp310"
    "cp311-cp311"
    "cp312-cp312"
    "cp313-cp313"
    "pp310-pypy310_pp73"
    "pp311-pypy311_pp73"
)
cd /io

# Compile wheels
for PYBIN in "${TARGET_PYBIN[@]}"; do
    /opt/python/${PYBIN}/bin/python -m venv /tmp/py-venv-${PYBIN}

    source /tmp/py-venv-${PYBIN}/bin/activate
    python -m pip install --no-cache-dir build Cython==3.1.2 setuptools wheel
    python -m build
    deactivate
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w dist/ \
        || echo "Skipping non-platform wheel $whl"
done

rm dist/*-linux_x86_64.whl
