#!/bin/bash

docker pull quay.io/pypa/manylinux2010_x86_64
docker run --rm -e PLAT=manylinux2010_x86_64 -v `pwd`:/io quay.io/pypa/manylinux2010_x86_64 /io/scripts/build-wheels.sh
