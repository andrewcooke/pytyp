#!/bin/bash

rm -fr doc-src/_build
pushd doc-src
PYTHONPATH=../src make html
popd
