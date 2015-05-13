#!/bin/bash

pushd ~/project/www/pytyp
svn update
svn remove --force *
svn commit -m "pytyp"
popd
rsync -rv --exclude=".svn" --delete doc-src/_build/html/ ~/project/www/pytyp
pushd ~/project/www/pytyp
svn add *
svn commit -m "pytyp"
popd

