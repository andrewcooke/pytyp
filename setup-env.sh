#!/bin/bash

rm -fr env
pyvenv-3.4 env
#virtualenv-3.4 -p /usr/local/bin/python3.2 --no-site-packages env
#virtualenv-3.4 -p /usr/bin/python3.4 --no-site-packages env
. env/bin/activate
easy_install pyyaml
easy_install nose
easy_install docutils
