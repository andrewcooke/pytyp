#!/bin/bash

find src -name "*.py" -exec sed -i -f delete-licence.sed \{} \;

