
.. automodule:: pytyp.spec.record

.. testsetup::

  from pytyp.spec.record import *

.. _verification:

Record Container
================

This module provides a container that combines aspects of ``dict``, ``tuple``
and ``object``.  It is implemented as a class factory, in a similar way to
`collections.namedtuple
<http://docs.python.org/py3k/library/collections.html?highlight=namedtuple#collections.namedtuple>`_,
and has the following features:

* The constructor can take defaults and type annotations; if type annotations
  are present they are checked by default.

* The constructor can used like a ``tuple``, or with named arguments like
  ``dict``.

* The generated class subclasses ``dict`` and so has the usual ``dict``
  iteration / read methods.

* Contents can be accessed via ``[]`` and also via attributes (it unifies the
  ``__getitem__()`` and the ``__getattr__()`` protocols).

* Optionally, instances can be read–only (immutable), in which case they are
  also hashable.

* Instances are fixed in size, containing only the entries specified in the
  constructor, unless an additional ``__`` argument is given (which can
  optionally specify a type for extra values).

.. autofunction:: record
