
Pytyp Package
=============

Pytyp can *encode* from Python classes to dicts.  It can also *decode* dicts
back into Python classes.

Although they are designed to work together, each of these processes has
different requirements.  If you only want to move data in one direction you
only need to comply with the requirements for that process.

Routines that use the encoding and decoding describe here to inter-operate
with JSON and YAML are available in the sub-packages :mod:`pytyp.json` and
:mod:`pytyp.yaml`.  The documentation in this section focusses on the
underlying implementation.

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

Implementation
--------------

The approach here is driven by practical considerations, but also tries to
maintain some contact with simple type theory:

 * Classes, tuples, named tuples and dicts are all treated as product types
   (in the case of classes, constructor arguments are used - this is intended
   to resemble data constructors in functional languages).

 * `Opt()` introduces optional types (aka maybe types; `None` is the
   alternative).  These are implicit on class contructor parameters with
   default values.

 * Lists are polymorphic (with a single type parameter).

 * All types are inclusional (subtypes are accepted as matches for
   supertypes).

 * Omitted types and explicit `None` type declarations are polymorphic, but
   tuples specify an exact length (additional values are accepted in dicts,
   but not in named tuples).

 * `Choice()` introduces sum (union) types.

The current implementation also attempts to respect "duck typing" of
collections as much as possible (a list type specification will match a tuple
of values if the contents are all of the correct type, for example).  This
feels "more Pythonic" (if anything here can be considered Pythonic...) but may
change in the future.

Type variables are not currently supported, but should be easy to add in the
next release.

.. autofunction:: Opt
.. autofunction:: Choice
.. autofunction:: dispatch

.. _strong_types:

Strong Types for Python
-----------------------

These are not static, and are probably not useful in practice (amongst other
problems, they are terribly inefficient), but given the infrastructure above
it seemed wrong not to include them.

.. autofunction:: checked
.. autofunction:: validate

Subpackages
-----------

.. toctree::

    pytyp.json
    pytyp.yaml

