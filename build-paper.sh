#!/bin/bash

rst2latex.py --documentoptions='10pt,a4paper,DIV=calc' --literal-block-env=lstlisting pytyp.rst pytyp.tex; pdflatex pytyp.tex
