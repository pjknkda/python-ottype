#!/bin/bash
set -e -x

TARGET_PYBIN=("cp37-cp37m" "cp38-cp38" "cp39-cp39")

# Compile wheels
for PYBIN in "${TARGET_PYBIN[@]}"; do
    "/opt/python/${PYBIN}/bin/pip" install Cython==0.29.24
    "/opt/python/${PYBIN}/bin/pip" wheel /io/ -w /io/dist
done

# Bundle external shared libraries into the wheels
for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/dist/ \
        || echo "Skipping non-platform wheel $whl"
done
