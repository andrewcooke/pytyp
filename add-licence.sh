#!/bin/bash

find src -name "*.py" -exec sed -i -f add-licence.sed \{} \;


