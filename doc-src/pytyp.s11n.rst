
Serialisation (pytyp.s11n)
==========================

Pytyp can *encode* from Python classes to dicts.  It can also *decode* dicts
back into Python classes.

Although they are designed to work together, each of these processes has
different requirements.  If you only want to move data in one direction you
only need to comply with the requirements for that process.  For more details
see :ref:`encoding` and :ref:`decoding`.

Routines that use the encoding and decoding described here to inter-operate
with JSON and YAML are available in the sub-packages :mod:`pytyp.s11n.json`
and :mod:`pytyp.s11n.yaml`.  The documentation for :mod:`pytyp.spec.abcs`
describes the type specifications that guide this process.

.. automodule:: pytyp.s11n

Subpackages
-----------

.. toctree::
   :maxdepth: 1

   pytyp.s11n.base
   pytyp.s11n.json
   pytyp.s11n.yaml
