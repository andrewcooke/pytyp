
Pytyp.json Module
=================

This module provides basic support for mapping JSON data to Python classes.

It does not provide:

 * Versioning of data

 * Encoding of the root type specification

but these features can be built on top of the functionality provided here, if
required.

.. automodule:: pytyp.json

Encoding
--------

.. autofunction:: dump
.. autofunction:: dumps
.. autodata:: JSONEncoder

Decoding
--------

.. autofunction:: make_load
.. autofunction:: make_loads
.. autofunction:: make_JSONDecoder

