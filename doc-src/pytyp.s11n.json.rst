
JSON Serialisation (pytyp.s11n.json)
====================================

This module extends the standard Python json library so that it can write and
return instances of Python classes.  This simplifies Python code that
interacts with JSON (you don't need to use dicts where you would normally use
a class, which means you can access values using attributes rather named
indices).

.. automodule:: pytyp.s11n.json

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

