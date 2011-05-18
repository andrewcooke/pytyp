
.. automodule:: pytyp.s11n.yaml

.. testsetup::

  from pytyp.s11n.yaml import *


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

Encoding
--------

.. tip::

   For background details see :ref:`encoding` and :ref:`type_specs`.

.. autofunction:: dump
.. autofunction:: dump_all

Decoding
--------

.. tip::

   For background details see :ref:`decoding` and :ref:`type_specs`.

.. autofunction:: make_load
.. autofunction:: make_load_all
