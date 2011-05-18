
.. automodule:: pytyp.s11n.json

.. testsetup::

  from pytyp.s11n.json import *

JSON Serialisation (pytyp.s11n.json)
====================================

This module extends the standard Python json library so that it can write and
return instances of Python classes.  This simplifies Python code that
interacts with JSON (you don't need to use dicts where you would normally use
a class, which means you can access values using attributes rather named
indices).

Encoding
--------

.. tip::

   For background details see :ref:`encoding` and :ref:`type_specs`.

.. autofunction:: dumps
.. autofunction:: dump
.. autodata:: JSONEncoder

Decoding
--------

.. tip::

   For background details see :ref:`decoding` and :ref:`type_specs`.

.. autofunction:: make_loads
.. autofunction:: make_load
.. autofunction:: make_JSONDecoder

