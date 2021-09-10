#!/bin/bash
set -e -x

TARGET_PYBIN=("cp37-cp37m" "cp38-cp38" "cp39-cp39")

# Install packages and test
for PYBIN in "${TARGET_PYBIN[@]}"; do    
    "/opt/python/${PYBIN}/bin/pip" install -e /io/.[dev]
    "/opt/python/${PYBIN}/bin/pytest" -v /io/
done
