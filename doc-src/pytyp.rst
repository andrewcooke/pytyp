
Pytyp Package
=============

Pytyp can *encode* from Python classes to dicts.  It can also *decode* dicts
back into Python classes.

Although they are designed to work together, each of these processes has
different requirements.  If you only want to move data in one direction you
only need to comply with the requirements for that process.

Routines that use the encoding and decoding describe here to inter-operate
with JSON and YAML are available in the sub-packages :mod:`pytyp.json` and
:mod:`pytyp.yaml`.  The documentation in this section and :mod:`pytyp.types`
focusses on the underlying implementation.

.. automodule:: pytyp

.. _encoding:

Encoding
--------

.. autodata:: DEFAULT_RAW
.. autofunction:: encode

.. _decoding:

Decoding
--------

.. autofunction:: decode

Subpackages
-----------

.. toctree::

    pytyp.json
    pytyp.yaml

