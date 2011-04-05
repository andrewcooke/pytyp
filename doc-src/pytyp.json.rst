
Pytyp.json Module
=================

This module extends the standard Python json library so that it can write and
return instances of Python classes.  This simplifies Python code that
interacts with JSON (you don't need to use dicts where you would normally use
a class, which means you can access values using attributes rather named
indices).

It does not provide:

 * versioning of data or

 * encoding of the root type specification

but these features can be built on top of the functionality provided here, if
required.

.. automodule:: pytyp.json

Encoding
--------

.. autofunction:: dumps
.. autofunction:: dump
.. autodata:: JSONEncoder

Decoding
--------

.. autofunction:: make_loads
.. autofunction:: make_load
.. autofunction:: make_JSONDecoder

