
Exploring Python's Types
========================

:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.1 of 13-04-2011

Abstract
--------

To do.

.. contents::
   :depth: 3

.. Disclaimer
   ----------

   For "historical reasons" the discussion of types systems and dynamic
   languages can be emotionally charged.  So here, at the start of my
   discussion, I want to assure you, gentle reader, that I do most of my
   programming (professional and private) in Python and have used it for many
   years.  My intentions are friendly.  I do not want to unfairly criticise or
   damage the language, or lead unwary learners of Python down a corrupt and
   un-Pythonic path.  I aim only to explore the boundaries of the language in
   a spirit of intellectual curiosity.


Introduction
------------

Apology
~~~~~~~

This paper is motivated by the development of a Python package called
``pytyp``, intended to improve the exchange of data between Python and JSON.
Although Python's ``json`` package supports moving data from one format to the
other it requires the use of "simple" collections.  With ``pytyp`` I wanted to
support user--defined classes in Python.

That work grew into a more general toolkit that explores the use of "types" in
Python data.  I became increasingly aware of the gap between "traditional"
type theory and the approach used in Python.

I am, I believe, sympathetic to the Python ethos.  I understand that it is
annoying when people attempt to "bolt on" ideas from other languages that
clearly do not fit.  But, at the same time, I enjoy pushing boundaries and
exploring new ideas.  This approach can be productive --- Zope is a wonderful
example of the best and worst --- and while I don't for a minute claim to be
working at such a level, I hope that recording and clarifying my experience
will help someone else.

Roadmap
~~~~~~~

In the first section, `Types in Python`_, I sketch how types work in Python.
Next, in `Pytyp`_, I describe "type specifications", which express collection
types in Python itself, how these connect with ideas from type theory, and how
they can be used in Python code.  Finally I discuss whether and how these two
approaches --- "Python as implemented" and "Pythonic algebraic types" --- can
be unified.

Types in Python
---------------

Python does not have a statically verified type system, but the language does
have a notion of types.

Classes and Attributes
~~~~~~~~~~~~~~~~~~~~~~

The principal tool for structuring source code is to define a ``class``.  This
specifies a set of attributes (directly and through inheritance) for class
instances (objects).  The class associated with an object is universally
referred to as its *type* and available at runtime via the ``type()``
function.

However, the attributes associated with an object are not fixed --- it is
possible to modify any instance through various mechanisms (including
meta-classes and direct manipulation of the underlying dictionaries) --- and
the language runtime does not use the object's type to guide execution [#]_.
Instead, each operation succeeds or fails depending on whether any necessary
attribute is present on the instance in question.

Even so, the notion that an instance's type is its class, and that this
describes how it will behave, is very useful in practice --- experienced
Python programmers still describe the behaviour of programs in terms of types
and classes.  This is because Python's extreme flexibility, although useful
and powerful, is rarely exploited.

.. [#] Except for immutable types, which exist partly so that the
   implementation *can* make such an assumption and so operate more
   efficiently.


Duck Typing
~~~~~~~~~~~

Despite the approach outlined above some operations appear to be specific to
certain types.  For example, the ``float()`` function only works for numerical
types (or strings that can be interpreted as numerical values).  But such
examples can generally be explained in terms of attribute access via "special"
methods (in the case of ``float()`` the method ``__float__()`` on the
function's argument).

I do not know if *every* operation can be explained in terms of attributes,
but my strong impression is that this is the intention: Python is designed to
describe all "type-related" runtime behaviour in terms of attribute access.
In this way it implements (and defines) "duck typing".

Recent Extensions
~~~~~~~~~~~~~~~~~

Work related to Python 3 extended the language in two interesting ways.

First, it addressed the conflict described above, which still exists in
theory, even if it is rarely important in practice: on the one hand,
programmers behave as though Python's runtime behaviour can be reliably
explained in terms of types; on the other, the runtime functions in terms of
available attributes.  Abstract Base Classes (ABCs) resolve this contradiction
by identifying collections of attributes as types.

Second, Python 3 supports (but does enforce) type annotations.  These are
metadata associated with functions.  For example, the following is valid
Python 3 code::

  def func(a: int, b:str) -> list:
      return [a, b]

Review
~~~~~~

A consistent, simple, global model of Python's runtime type system exists.  It
is called "duck typing" and, as described above, uses the availability of
object attributes.

Recent work has started to build on this foundation by reifying collections of
attributes (ABCs) and allowing metdata (formatted in a manner traditionally
associated with types) to be specified on functions.

But there are still many open questions:

* How can we best use the tools we have?  How should type-related metadata be
  used?  Are there more compact ways of expressing types in common cases?

* How do types in Python connect with other uses?  How do they match common
  abstractions used in other languages?  What about common abstractions used
  in type theory?

* How can types in Python help programmers?  Is static type verification
  possible and useful?  Can types help write more declarative code?

* What is missing from Python (and would be useful to have)?  What language
  changes would help future work?
 
Pytyp
-----

This is the main section of the paper, in which I explore possible extensions
to Python.  These extensions are, largely, implemented in the ``pytyp``
library but my argument is more general: this is not an introduction to
``pytyp``; rather it is a "thought experiment" that happens to have been
implemented (in parts).

Typed Collections
~~~~~~~~~~~~~~~~~

How do we define the type of a list of values?  Or a dictionary?  What if the
contents are an inhomogenous set of types?

To answer these questions using tools from the previous section we would start
with the appropriate container ABC.  But that only defines the attributes (ie
that we have suitable methods to treat the container as a list, or a
dictionary --- more correctly, as a ``Sequence`` or ``Mapping``, which are
ABCs defined in the ``collections`` package).  To define the contents we must
also assume that type annotations are being used::

  class IntSequence(Sequence):
      def __next__() -> int:
          return super(IntSequence, self).__iter__(index)

This has some problems (it's verbose, particularly when all methods are
defined; type annotations don't exist for generators [#]_; it's unclear how it
can be backfitted to handle data from some existing API; type annotations are
not "used"), but is, I hope, a fair extrapolation of Python's current
approach.

.. [#] http://mail.python.org/pipermail/python-3000/2006-May/002103.html

One of these problems is easy to fix: we can define a simpler syntax:
``[int]`` or, more formally, ``Seq(int)`` [#]_.

.. [#] The ``normalize()`` function in ``pytyp`` will convert the first
   expression to the second, but there is little reason to do so unless
   ``pytyp`` is extended to include literal values (the distinction between
   "values" and "types" then becomes important --- we might be referring to a
   value that is a list containing a single value, which happens to be
   ``int``).

This "natural" syntax can be extended to inhomogenous collections:
dictionaries look like ``{'a':int, 'b':str}``; tuples look like ``(int,
str)``.  But these representations appear [#]_ tied to specific classes,
rather than the ``Mapping`` ABC.  A better syntax might be ``Map(a=int,
b=str)`` or ``Map(int, str)`` (where integer indices are implicit).
   
The step from sequences to maps is more significant than a simple change of
syntax.  When we try to translate the map syntax back into ABCs we find that
we need dependent types (the type returned by ``__getitem__`` depends on the
index argument).  This is a consequence of Python using a parametric approach
to records via ``__getitem__()`` [#]_.

.. [#] This does not "feel" wrong to me; it seems natural that a language with
   dynamic features like those in Python will have dependent types.  What is
   more worrying is how this might affect efficiency.

A Little Formality
~~~~~~~~~~~~~~~~~~

The standard toolbox of "statically typed" languages contains three core
components: product types; sum types; parametric polymorphism.

Product Types
.............

The way that maps are handled above (particularly when using the ``Map(a=int,
b=str)`` syntax) is very close to the concept of product types: a container
with a fixed number of values (referenced by label or index) each have a
distinct type.  All that is missing is a name (ie. the approach here, at least
in isolation, is structural).

In Python, when we associate a name with a dict, we are typically defining a
class.  So it is not surprising that extending our discussion to include
classes brings us closer to product types.  However, at least in the simple
approach here, it also requires a significant simplifying assumption: that the
constructor arguments are present as instance attributes.

In other words, a product type in Python looks like this::

  class MyProduct:
      def __init__(self, a: int, b:str):
          self.a = a
          self.b = b

Compared to ``Map(a=int, b=str)`` this has an advantage --- it is named ---
but also some disadvantages (more fairly, it introduces some new
complications).

First is a syntactic annoyance: in a a type specification it would be written
as ``MyProduct`` [#]_ which hides the types.  But how can this be otherwise?

.. [#] In ``pytyp`` this can also be written more formally as
   ``Cls(MyProduct)``.

Next, access to record values is via attributes rather than ``__getitem__()``.
In a sense, this is an improvement: it ties more directly to Python's duck
typing (although cumbersome --- we are constraining the return type of a
property's ``__get__()`` function --- it avoids dependent types).  But it
complicates any kind of unification with the structural approach of ``Map()``.

Finally, as already mentioned, the "simplifying assumption" is a significant
restriction.


Sum Types
.........

Polymorphism
............

Unbounded polymorphism can be specified in ``pytyp`` using ``...`` (ellipsis,
a singleton intended for use in array access, but available generally in
Python 3's grammar).  For example, ``[...]`` denotes a list of any type.

Parametric polymorphism surprisingly easy.  The type system we are sketching
is embedded in Python, so we can use Python's own functions::

  def polymorphic_list(param):
      return [param]

In `A Tree Functor`_ the same approach approximates an ML functor.

Examples
~~~~~~~~

Type Verification
.................

The ``checked`` decorator verifies parameters and return values against the
specification in the type annotation::

  >>> @checked
  ... def str_len(s:str) -> int:
  ...     return len(s)
  >>> str_len('abc')
  3
  >>> str_len([1,2,3])
  Traceback (most recent call last):
    ...
  TypeError: Value inconsistent with type: [1, 2, 3]!:<class 'str'>


JSON Decoding
.............

A Tree Functor
..............

Conclusions
-----------

Discussion Points
~~~~~~~~~~~~~~~~~

Dependent Annotations
.....................

How do we get from ``[int]`` to the code outlined in `Typed Collections`_?  We
can use a function, similar to the handling of polymorphism and functors
above.  Perhaps ABCs themselves should be parameterised?  This would codify a
particular relationship between the type annotations of different methods.
The same idea, in more general terms can be phrased as "how should information
be shared between type annotations on a class?"  One answer might be to allow
them access to attributes defined on ``self``.

Attributes
..........



Named tuples.

Structural and Duck Typing
..........................

Naively expected structural typing to fit better with duck typing - after all,
whether an attrobute exists or not is very structural.  But there is a tension
between ``Map()`` and ``MyProduct`` (or between attributes and dicts)
that.... what?  Python's collections seem to require structural typing.  It's
classes do not.

Efficiency
..........

The ``pytyp`` package is implemented in Python.  This makes it flexible, but
extremely inefficient.  For the occasional type check when debugging this is
not an issue, but the features described above are not suitable for use
throughout a large Python application.

Performance could be improved by caching in some areas.  In type dispatch it
might be possible to "precompile" the tests, reducing them to the minimum
needed to differentiate (rather than verify, which requires a recursive
exploration of the entire value) the different types.

How could performance be improved if some functionality was moved to the
implementation?  What would minimal support require?  Perhaps caching would be
simplified by allowing arbitrary tags on values?  Are there useful parallels
between type verification and the "unexpected path" handling of a dynamic
language JIT compiler?
