#!/bin/bash

#rst2latex.py --documentoptions='10pt,paper=A4,DIV=8,headinclude=false,footinclude=false,twoside=false' --literal-block-env=lstlisting pytyp.rst pytyp.tex; pdflatex pytyp.tex
rst2latex.py --documentoptions='10pt,paper=A4,DIV=20,headinclude=false,footinclude=false,twoside=false,twocolumn=true' --literal-block-env=lstlisting pytyp.rst pytyp.tex; pdflatex pytyp.tex
