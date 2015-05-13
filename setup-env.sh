#!/bin/bash

rm -fr env
# this is just the virtualenv for 3 that my opensuse has by default
#virtualenv-3.4 -p /usr/local/bin/python3.2 --no-site-packages env
virtualenv-3.4 -p /usr/bin/python3.4 --no-site-packages env
. env/bin/activate
easy_install pyyaml
easy_install nose
easy_install docutils
