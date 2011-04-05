
.. _type_specs:

Pytyp.spec Module
=================

This module provides support for the type specifications that define how to
construct Python objects from dicts.  It also provides a simple type
verification system for Python.

.. automodule:: pytyp.spec

Overview
--------

A type specification is a "picture" of the types used to form a value.  It is
restricted to a class or a collection (list, tuple or dict, perhaps nested) of
classes.

So, for example `[MyClass]` is the definition for a sequence (`list` or
`tuple`) of `MyClass` instances.  And `{'a':str, 'b':Opt(MyClass)}` is a
`dict` with two keys (the latter optional); the key `'a'` maps to a string and
key `'b'` maps to either `None` or a `MyClass` instance.

Sometimes, however, we want to specify types over a larger range of connected
values.  For example, what are the types of the arguments supplied to
`MyClass`?  These cannot be given in a single type specification.  Instead, to
handle this case, we add further specifications to class constructors.  So
`MyClass` might be defined as::

  class MyClass():
      def __init__(foo:str, bar:AnotherClass):
          ...

which indicates that `MyClass()` takes two arguments - a string and an
`AnotherClass` instance.

In this way the system can piece together the types across an extended set of
connected objects.

Slightly more formal description
--------------------------------

The approach here is driven by practical considerations, but also tries to
maintain some contact with simple type theory:

 * Simple values are described by the Python type (eg. `str` for a string).
   Classes are described by the appropriate constructor.

 * Explicit `None` type declarations match any value, but do require a value.

 * Dicts define product types with named fields (which can match dicts).

 * Tuples define product types with indexed fields (which can match lists,
   tuples and iterables).

 * Lists with a single entry define sequences (which can match lists, tuples
   and iterables) of any length.

 * `Choice()` introduces sum (union) types.

 * `Opt()` introduces optional types (aka maybe types; `None` is the
   alternative).

 * All types are inclusional (subtypes are accepted as matches for
   supertypes).

The current implementation attempts to respect "duck typing" of collections as
much as possible (defining types for "sequences" rather than only lists, for
example).

On verification (see below):

 * The number and type of product type fields are checked, but `Opt()` entries
   may be omitted with *named* fields.  Note: This only works for "direct"
   `Opt()` specifications; an `Opt()` inside a `Choice()` will not work (there
   are two different underlying mechanisms - one for "maybe" types and one for
   missing fields; using a single annotation for both makes specifications
   simpler, but the downside is this apparent inconsistency).

 * All sequence values must match the type defined for the sequence.
   Iterables will be expanded to lists and so are "used" (this makes the use
   of verification with iterables self-defeating).

 * Alternatives in a `Choice()` are checked in order (left to right) until a
   match is found for the contents.  No backtracking occurs if subsequent
   alternatives fail.

Type variables are not currently supported, but should be easy to add in the
next release.

.. warning::

  In pytyp 1.1 I have revised how *named* product types are handled.  They can
  no longer be defined with named tuples (which, if used in type
  specifications, are treated as "ordinary" tuples).  A dict specification can
  still be used and is now more precise, requiring an exact match unless
  optional fields are present.  An optional type in a named product can verify
  a value of the correct type (as before), `None` (as before), or a
  compeletely omitted value (new).  So a dict will not accept additional
  fields, but may miss optional fields.  This simplifies the system while
  remaining consistent with how I see the library being used to parse
  configuration files.

.. autofunction:: dispatch

.. _strong_types:

Stronger Types for Python
-------------------------

These are not static, and are probably not useful in practice (amongst other
problems, they are terribly inefficient), but given the infrastructure above
it seemed wrong not to include them.

.. autofunction:: checked
.. autofunction:: verify
.. autofunction:: Opt
.. autofunction:: Choice
.. autofunction:: class_to_dict_spec
