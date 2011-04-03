#!/bin/bash

virtualenv3 -p /usr/local/bin/python3.2 --no-site-packages env
. env/bin/activate
easy_install pyyaml
