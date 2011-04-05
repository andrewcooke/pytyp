#!/bin/bash

pushd ~/projects/personal/www/pytyp
svn update
svn remove --force *
svn commit -m "pytyp"
popd
rsync -rv --exclude=".svn" --delete doc-src/_build/html/ ~/projects/personal/www/pytyp
pushd ~/projects/personal/www/pytyp
svn add *
svn commit -m "pytyp"
popd

