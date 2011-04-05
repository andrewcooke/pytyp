
Pytyp.yaml Module
=================

This module extends the popular PyYAML library so that it can write and return
instances of Python classes.  This simplifies Python code that interacts with
YAML (you don't need to use dicts where you would normally use a class, which
means you can access values using attributes rather than named indices).

It does not provide:

 * versioning of data or

 * encoding of the root type specification

but these features can be built on top of the functionality provided here, if
required (PyYAML also supports an encoding that embeds the Python type).

.. warning::

  This module requires `PyYAML <http://pyyaml.org/wiki/PyYAML>`_.  If that
  package is not present then the functionality defined here will not be
  available.

.. automodule:: pytyp.yaml

Encoding
--------

.. autofunction:: dump
.. autofunction:: dump_all

Decoding
--------

.. autofunction:: make_load
.. autofunction:: make_load_all
