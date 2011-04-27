#!/bin/bash

export PYTHONPATH=src
nosetests --with-doctest `find src -name "*.py"`
echo -n "paper: "
python -m pytyp.spec._test.paper
