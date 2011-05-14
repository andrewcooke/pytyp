
Introduction (pytyp)
====================

Pytyp is a library of useful Python utilities that are loosely based on
the "types" of objects.

The most important of these support encoding and decoding data to and from
:mod:`JSON <pytyp.s11n.json>` and :mod:`YAML <pytyp.s11n.yaml>`.  Pytyp
extends the standard support (which works for lists and dicts) to handle
user-defined Python classes.

For more information on object serialization see :mod:`pytyp.s11n`.

Pytyp contains some more "experimental" code that extends the work used to
support JSON and YAML encoding and explores how a "stronger typed" Python
might work.

For more information on type-related experiments see :mod:`pytyp.spec`.

.. automodule:: pytyp

Subpackages
-----------

.. toctree::
   :maxdepth: 1

   pytyp.s11n
   pytyp.spec
   pytyp.util

