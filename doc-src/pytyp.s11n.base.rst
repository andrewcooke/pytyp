
Serialisation Support (pytyp.s11n.base)
=======================================

Pytyp can *encode* from Python classes to dicts.  It can also *decode* dicts
back into Python classes.

The functions and classes here form the basis for :mod:`pytyp.s11n.json` and
:mod:`pytyp.s11n.yaml` - you may find the examples here useful in
understanding how the process works, but probably want to call the routines in
those packages.

.. automodule:: pytyp.s11n.base

.. _encoding:

Encoding Support
----------------

To encode data, pytyp looks at the constructor arguments.  For each
argument it assumes that the class has an attribute or property that
provides a value.

So, for example, this class can be encoded::

  >>> class EncExample():
  ...     def __init__(self, a, b=None):
  ...         self.a = a
  ...         self.b = b
  ...
  >>> encode = Encoder()
  >>> encode(EncExample(1, 2))
  {'a': 1, 'b': 2}

but this class cannot::

  >>> class BadEncExample():
  ...     def __init__(self, q):
  ...         self.z = q
  ...
  >>> encode(BadEncExample(1))
  Traceback (most recent call last):
    ...
  AttributeError: 'BadEncExample' object has no attribute 'q'

If you do not want your objects to be mutable you can expose the same
information through read-only properties::

  >>> class ReadOnly():
  ...     def __init__(self, value):
  ...         self._value = value
  ...     @property
  ...     def value(self):
  ...         return self._value
  ...
  >>> encode(ReadOnly(1))
  {'value': 1}

.. autoclass:: Encoder

.. _decoding:

Decoding Support
----------------

To decode data, pytyp looks at the type specification and constructs
the class by calling the constructor.  The specification can contain
lists, tuples and dictionaries, but must have the same form as the input.

For example, here `decode()` is called with a type specification for a
list of `DecExample()` instances::

  >>> class DecExample():
  ...     def __init__(self, a):
  ...         self.a = a
  ...     def __repr__(self):
  ...         return '<DecExample({0})>'.format(self.a)
  ...
  >>> decode([{'a': 1}, {'a': 2}], [DecExample])
  [<DecExample(1)>, <DecExample(2)>]

To handle nested types the constructor of the container class must have
a type declaration (another type specification)::

  >>> class Container():
  ...     def __init__(self, ex:DecExample):
  ...         self.ex = ex
  ...     def __repr__(self):
  ...         return '<Container({0})>'.format(self.ex)
  ...
  >>> decode({'ex': {'a': 1}}, Container)
  <Container(<DecExample(1)>)>

Note the type declaration in the constructor above.  Without that
declaration pytyp will incorrectly interpret the data::

  >>> class BadContainer():
  ...     def __init__(self, ex):
  ...         self.ex = ex
  ...     def __repr__(self):
  ...         return '<BadContainer({0})>'.format(self.ex)
  ...
  >>> decode({'ex': {'a': 1}}, BadContainer)
  <BadContainer({'a': 1})>

In type specifications, lists must be of a single type, but tuples and
dicts have a specific type for each member::

  >>> decode(({'ex': {'a': 1}}, {'a': 2}), (Container, DecExample))
  (<Container(<DecExample(1)>)>, <DecExample(2)>)

A value of None can be matched by an optional type::

  >>> from pytyp.spec.abcs import Opt
  >>> decode((None, {'a': 2}), (Opt(Container), DecExample))
  (None, <DecExample(2)>)

.. autofunction:: decode
