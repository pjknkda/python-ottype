#!/bin/bash
set -e -x

TARGET_PYBIN=("cp37-cp37m" "cp38-cp38")

# Compile wheels
for PYBIN in "${TARGET_PYBIN[@]}"; do
    "/opt/python/${PYBIN}/bin/pip" install -e /io/.[dev]
    "/opt/python/${PYBIN}/bin/pip" wheel /io/ -w /io/dist
done

# Bundle external shared libraries into the wheels
for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/dist/ \
        || echo "Skipping non-platform wheel $whl"
done

# Install packages and (test)
for PYBIN in "${TARGET_PYBIN[@]}"; do
    "/opt/python/${PYBIN}/bin/pip" install python-ottype --no-index -f /io/dist
    # "/opt/python/${PYBIN}/bin/pytest" python-ottype
done
