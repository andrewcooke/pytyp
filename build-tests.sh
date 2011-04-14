#!/bin/bash

export PYTHONPATH=src
nosetests --with-doctest `find src -name "*.py"`
