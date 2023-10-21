#!/bin/bash
set -e -x

TARGET_PYBIN=("cp38-cp38" "cp39-cp39" "cp310-cp310" "cp311-cp311")
cd /io

# Compile wheels
for PYBIN in "${TARGET_PYBIN[@]}"; do
    /opt/python/${PYBIN}/bin/python -m venv /tmp/py-venv-${PYBIN}

    source /tmp/py-venv-${PYBIN}/bin/activate
    python -m pip install --no-cache-dir Cython==3.0.4 wheel
    python -m pip wheel . -w dist/
    deactivate
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w dist/ \
        || echo "Skipping non-platform wheel $whl"
done
