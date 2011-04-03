#!/bin/bash

rm -fr doc

pushd doc-src
make html
popd
