#!/bin/bash

rm -fr doc-src/_build
pushd doc-src
PYTHONPATH=../src make html
PYTHONPATH=../src make doctest
popd
