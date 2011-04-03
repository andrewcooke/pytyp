
Pytyp.yaml Module
=================

This module provides basic support for mapping YAML data to Python classes.

It does not provide:

 * Versioning of data

 * Encoding of the root type specification

but these features can be built on top of the functionality provided here, if
required (pyyaml also supports an encoding that embeds the Python type).

.. warning::

  This module requires `pyyaml <http://pyyaml.org/wiki/PyYAML>`_.  If that
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
