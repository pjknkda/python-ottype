#!/bin/bash

docker run --rm -e PLAT=manylinux2010_x86_64 -v `pwd`:/io quay.io/pypa/manylinux2010_x86_64 /io/build-wheels.sh
