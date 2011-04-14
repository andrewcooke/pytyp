
YAML Serialisation (pytyp.s11n.yaml)
====================================

This module extends the popular PyYAML library so that it can write and return
instances of Python classes.  This simplifies Python code that interacts with
YAML (you don't need to use dicts where you would normally use a class, which
means you can access values using attributes rather than named indices).

.. warning::

  This module requires `PyYAML <http://pyyaml.org/wiki/PyYAML>`_.  If that
  package is not present then the functionality defined here will not be
  available.

.. automodule:: pytyp.s11n.yaml

Encoding
--------

.. autofunction:: dump
.. autofunction:: dump_all

Decoding
--------

.. autofunction:: make_load
.. autofunction:: make_load_all
