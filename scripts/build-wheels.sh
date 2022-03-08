#!/bin/bash
set -e -x

TARGET_PYBIN=("cp37-cp37m" "cp38-cp38" "cp39-cp39" "cp310-cp310")
cd /io

# Compile wheels
for PYBIN in "${TARGET_PYBIN[@]}"; do
    "/opt/python/${PYBIN}/bin/pip" install Cython==0.29.24
    "/opt/python/${PYBIN}/bin/pip" wheel . -w dist/
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w dist/ \
        || echo "Skipping non-platform wheel $whl"
done
