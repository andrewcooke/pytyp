
.. raw:: latex

  \renewcommand{\ttdefault}{txtt}
  \lstset{language=Python,
	  morekeywords=[1]{yield}
  }
  \lstloadlanguages{Python}
  \lstset{
    basicstyle=\small\ttfamily,
    keywordstyle=\bfseries,
    commentstyle=\rmfamily\itshape,
    stringstyle=\slshape,
  }
  \lstset{showstringspaces=false}
  \lstset{columns=fixed,
       basewidth={0.5em,0.4em}}


Polymorphic ABCs
================

:Subtitle: Exploring Types in Python
:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.3 of 17-04-2011

Abstract
--------

To do.

.. contents::
   :depth: 2

Introduction
------------

Context
~~~~~~~

This all start as an attempt to improve JSON / Python inter-operability.  That
used some type–related code that naturally led to verification of type
annotations.  At which point I started writing this paper to record my
internal dialogue about how types could be extended in Python.

The paper then took on a life of its own and I rewrote the library to match
the most consistent approach I could find.

So this is an exploration of one way to extend "types" in Python.  The end
result is implemented in a library called ``pytyp``.

Roadmap
~~~~~~~

In the first section, `Current Status`_, I sketch Python's runtime type
support.  This shows how ABCs provide a clear, general model for duck typing.

`A Pythonic Extension`_ then explores possible exntensions, motivated by a
need to describe collections of data.  The first few sub-sections are
speculative; the issues are clarified in an `Implementation`_ and illustrated
with `Examples`_.

[Needs fixing once done]

Terminology
~~~~~~~~~~~

Many terms used to discuss types have specific meanings related to the
verification of program properties.  In this paper I am addressing a different
subject [#]_.  This means that I will often use the word "type" in a poorly
defined way.  When I need more precision I will use "(static) type system"
(about which one can reliably reason without executing code), "type
specification" (metadata using ABCs to describe Python classes), and "duck
types" (a model of runtime behaviour using available attributes).

.. [#] Although, in the section `A Little Formality`_, I discuss how type
   systems can guide type specifications.

Current Status
--------------

Python does not have a static type system [#]_, but the language does have a
notion of types.

.. [#] In the sense defined in `Terminology`_.

Classes and Attributes
~~~~~~~~~~~~~~~~~~~~~~

The principal abstraction for structuring source code is ``class``.  This
specifies a set of attributes (directly and through inheritance) for classes
and their instances (objects).  The class associated with an object is
universally referred to as its type and available at runtime via the
``type()`` function [#]_.

.. [#] I ignore Python 1 and 2 here.

However, the attributes associated with an object are not fixed — it is
possible to modify objects through various mechanisms (including meta-classes
and direct manipulation of the underlying dictionaries) — and the language
runtime does not use the object's class to guide execution [#]_.  Instead, each
operation succeeds or fails depending on whether any necessary attribute is
present on the instance in question.

Even so, the notion that an instance's type is its class, and that this
describes how it will behave, is very useful in practice — experienced
Python programmers still describe the behaviour of programs in terms of types
and classes.  This is because Python's extreme flexibility, although useful
and powerful, is rarely exploited.

.. [#] Except for immutable types, which exist partly so that the
   implementation *can* make such an assumption and so operate more
   efficiently.

Duck Typing
~~~~~~~~~~~

Despite the approach outlined above some operations still appear specific to
certain class instances.  For example, the ``float()`` function only works for
numerical types (or strings that can be interpreted as numerical values).  But
such examples can generally be explained in terms of attribute access via
"special" methods (in the case of ``float()`` the method ``__float__()`` on
the function's argument).

I do not know if *every* operation can be explained in terms of attributes,
but my strong impression is that this is the intention: **Python's runtime
behaviour can be modelled in terms of attribute access**.  In this way it
implements (and defines) duck typing.

Recent Extensions
~~~~~~~~~~~~~~~~~

Recent work has extended the language in two interesting ways.

First, it addressed the conflict described above: on the one hand, programmers
behave as though Python's runtime behaviour can be reliably explained in terms
of types; on the other, the runtime functions in terms of available
attributes.  Abstract Base Classes (ABCs) resolve this by identifying
collections of attributes, providing a class–like abstraction that is better
suited to duck typing.

However, Python still does not support the runtime *verification* of arbitrary
duck types [#]_::

  >>> class MyAbc(metaclass=ABCMeta):
  ...     @abstractmethod
  ...     def foo(self): pass
  >>> class MyExample:
  ...     def foo(self): return 42
  >>> isinstance(MyExample(), MyAbc)
  False

.. [#] Except by explicitly checking all attributes through introspection
   or, more usually, by trying an operation and then handling any exception.

Instead, ``MyExample`` must either subclass ``MyAbc`` or "register" itself
(populating a lookup table used by ``isinstance()``).  So ABCs provide
"witness typing" since **the ABC acts only as a witness to the veracity of the
registered (or subclass) type; it does not perform a runtime check of the
attributes** [#]_.

.. [#] No connection with witness types in Haskell is implied, although the
   idea is loosely related.

Second, Python 3 supports (but does enforce) type annotations.  These are
metadata associated with functions [#]_.  For example, the following is
valid::

  def func(a:int, b:str) -> list:
      return [a, b]

.. [#] Python docs call them "function annotations", but the use cases in
   PEP3107 all refer to types (the PEP does not explain why only functions
   were considered, except that generator annotations were "ugly").

Type annotations are not interpreted or enforced by the language runtime.
They are added to the function metadata and exposed through Python's
``inspect`` package.

Summary
~~~~~~~

A consistent, simple, global model of Python's runtime type system exists.  It
is called "duck typing" and, as described above, depends on the availability
of object attributes.

Recent work has started to build on this foundation by reifying collections of
attributes (ABCs) and allowing metdata (formatted in a manner traditionally
associated with types) to be specified on functions.  However, ABCs act only
as a witness to types (an unverified tag); they do not perform any runtime
checks.

Discussion
----------

Typed Collections
~~~~~~~~~~~~~~~~~

Syntax
......

To motivate our exploration consider the following questions.  How do we
define the type of a list of values?  Or a dictionary?  What if the contents
are drawn from an inhomogenous set of types?

Answering these with tools from the previous section would start with the
appropriate container ABC.  This defines the attributes used to access the
data.  To define the contents we could then add type annotations::

  class IntSequence(Sequence):
      def __getitem__(index) -> int:
          return super(IntSequence, self).__getitem__(index)
      ...

This has some problems [#]_, but is, I hope, a fair extrapolation of Python's
current approach.

.. [#] It is verbose, particularly when all methods are defined; type
   annotations don't exist for generators
   http://mail.python.org/pipermail/python-3000/2006-May/002103.html; it's
   unclear how to backfit types to an existing API; type annotations are not
   "implemented"; as is normal with current type systems it supports only
   homogenous sequences.
   
One problem is easy to fix.  We can define a simpler syntax: ``[int]`` or,
more formally, ``Seq(int)``.  I will call this a *type specification*.

This can be extended to inhomogenous collections: dictionaries would look like
``{'a':int, 'b':str}``; tuples like ``(int, str)``.  And since it would make
sense to use the ABC ``Mapping`` a better syntax might be ``Map(a=int,
b=str)`` or ``Map(int, str)`` with implicit integer indices for positional
arguments.

But we have a problem: the step from sequences to maps was more significant
than a simple change of syntax.  **When we try to translate** ``Map()`` **back
into ABCs with type annotations we find that we need dependent types**.  The
type of the return value from ``__getitem__(key)`` depends on the argument,
``key``.

Nice syntax; shame about the semantics.

Semantics
.........

To improve the semanics we must consider how a type specification is
used.  For example, we might intend to enforce runtime checking of function
arguments, or to specify how data can be transcoded.

On reflection (and experimentation) I can find three broad uses for type
specifications: verification; identification; and expansion.

**Verification** of a value's type (against some declaration) can be performed
in various ways.  We might examine the value structurally, comparing it
against the type specification piece by piece.  This approach seems best
suited to "data" types (lists, tuples and dictionaries) which tend to be used
in a polymorphic manner.  Alternatively, we can use witness typing, which
seems more suited to user–defined classes.

**Identification** of a value's type, although superficially similar to
verfication, is a harder problem.  In some simpler cases we may have a set of
candidate types, in which case we can verify them in turn; in other cases the
instance's class may inherit from one or more ABCs (this would still need
extending to include type information); but I don't see a good, "pythonic"
solution to the general problem.  Perhaps type witnesses (ABCs extended to
include type information) could pool registry information?

**Expansion** of a value by type covers a variety of uses where we want to
operate on some sub-set of the data and, perhaps, recombine the results.  One
example is to automate mapping between ``dict`` and user–defined classes.
Another is structural type verification.

Setting identification aside, we seem to have two possible semantics: one
structural; the other based on witnesses.

A Little Formality
~~~~~~~~~~~~~~~~~~

I will now explore how type specifications fit within three core concepts of
type theory: parametric polymorphism; product types; and sum types.

Parametric Polymorphism
.......................

Since we started with data structurs we have already addressed this:
``Seq(x)`` is polymorphic in ``x``, for example.  However, it's worth drawing
attention to an important point: **polymorphism occurs naturally in Python
data structures at the level of instances, not classes**.  This contrasts with
the current implementation of witness typing, ABCs, which is at the class
level.

So the idea that ``isinstance([1,2,3], Seq(int))`` should return ``True``
implies a significant change to the language semantics — ``isinstance()``
would depend on the *state* of an instance as well as its class.  The
relationship between ``isinstance()`` and ``issubclass()`` would shift: the
former could no longer be expressed in terms of the latter.

Product Types
.............

The handling of maps above (particularly when using the ``Map(a=int, b=str)``
syntax) is very close to the concept of product types: a container with a
fixed number of values (referenced by label or index), each with a distinct
type.

However, ``Map()`` only addresses dicts and tuples.  What about general
classes?  With a significant simplifying assumption — that the constructor
arguments are present as instance attributes — we can defined a
"class–like" product type in Python::

  class MyProduct:
      def __init__(self, a:int, b:str):
          self.a = a
          self.b = b

Incidentally, this has an advantage over ``Map()``: it does not require
dependent types when reduced to ABCs.  This is because each attribute would be
described separately, and so could have its own type.

And isn't this familiar?  It's very like named tuples.  Except that they are
second class citizens that don't directly support type annotations...

Sum Types
.........

The only Python feature I can find that is related to sum types is the idea
that ``None`` indicates a missing value, similar to the ``Maybe`` type.

If we need this concept we can use the notation ``Alt(a=int, b=str)`` (the
optional labels might be used for dispatch by type, with a case–like syntax,
for example).

Summary
~~~~~~~

This section has introduced a syntax that can describe parametric polymorphism
within Python code, largely at the instance level.  It is flexible enough to
handle basic concepts from type theory (roughly translated into Python's
runtime context).

Providing a semantics for these type specifications, particularly one related
to existing features, is more complex.  In particular, adding type annotations
to ABCs faces significant problems.  First, it is incomplete: attributes and
generators do not support annotations, and scope issues complicate some common
uses.  Second, dependent types would be needed to handle ``dict``.  Third, it
is verbose, particularly when using the standard container classes, which must
to be subclassed for every distinct use, but also because it ignores
correlations between the types of different attributes.

Registration (witness typing) is more promising, but cannot handle all cases;
a general solution will also require a structural (piecewise inspection)
approach.

In fact, the structural and witness semantics are complementary: witnesses
would work well for user-defined classes; structural typing is better suited
to Python's built–in container types.  There is a trade–off between
convenience and speed: where necessary built–in containers can be replaced by
immutable, registered custom classes.

Implementation
--------------

Approach
~~~~~~~~

The previous sections explored a variety of ideas.  Now I will describe the
``pytyp`` library.  This supports two general uses, identified in `Semantics`_
above: verification and expansion.

Two approaches to verification have been discussed: witnesses are efficient
but restricted to hashable classes; a structural approach allows the library
to also work with Python's common, mutable data structures.  ``Pytyp``
supports both.

ABCs
~~~~

Existing ABCs can be used in two ways: by inheritance or registration.  We can
preserve this while adding parametric polymorphism by creating subclasses to
contain the extra type information.  So, hypothetically, ``Sequence(int)``
would create (or retrieve from a cache, if it already exists) a subclass of
the existing ABC ``Sequence``, parameterised by ``int``, which would support
both subclassing and registration.

Inheritance
...........

In practice, because ``pytyp`` is a library, we cannot modify existing ABCs
directly [#]_, leading to an additional level of classes.

.. [#] It would be possible for the library to define a completely new set of
   ABCs, but this would make it harder to integrate with existing code.

So ``Seq`` subclasses ``Sequence`` and ``Seq(int)`` creates a subclass of
``Seq`` specialised to represent ``int`` sequences, which can itself be
subclassed::

    >>> class MyIntList(list, Seq(int)): pass
    >>> isinstance(MyIntList(), Seq(int))
    True
    >>> isinstance(MyIntList(), Sequence)
    True
    >>> isinstance(MyIntList(), Seq(float))
    False

Registration
............

We must extend registration to include instances.  This implies an extra cache
in the ABCs and a modification to the code that implements ``isinstance()``.

Extending ``isinstance()`` is difficult: despite the language in PEP 3119 [#]_
and Issue 1708353 [#]_, ``__instancecheck__()`` can only be over–ridden *on
the metaclass* [#]_.  Since providing a new metaclass would break inheritance
of the existing ABCs ``pytyp`` uses a "monkey patch" to delegate to
``__instancehook__()`` [#]_ on the class, if defined.

With this in place, registration works as expected::

    >>> Seq(int).register_instance(random_object)
    >>> isinstance(random_object, Seq(int))
    True

.. [#] http://www.python.org/dev/peps/pep-3119/
.. [#] http://bugs.python.org/issue1708353
.. [#] http://docs.python.org/reference/datamodel.html#customizing-instance-and-subclass-checks
.. [#] Named to resemble ``__subclasshook__()``, used for ``issubclass()`` 
   which *is* already supported (as noted earlier, before this work the two
   were largely equivalent).

Structural Typing
.................

Unfortunately, neither approach above will help with a list of integers,
``[1,2,3]``.  Subclassing is not useful (``list`` already exists, and anyway
we need this to work at the instance level) and registration fails (the value
cannot be hashed).

In cases like this we must fall back to structural verification — each entry
is checked in turn.  This is inefficient, of course, so the programmer must
consider whether it is appropriate::

    >>> isinstance([1,2,3], Seq(int))
    True

Expansion
~~~~~~~~~

Expansion can be implemented as a recursive exploration of the graph implicit
in the type specification.  Callbacks allow values to be processed; these can
recurse on their contents, giving the caller control over exactly what values
are "atomic".  Exceptions are made available to the callback by providing the
data as generators.

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
  TypeError: Value [1, 2, 3] inconsistent with type str.

JSON Decoding
.............

Here JSON data, expressed using generic data–structures, is decoded into
Python classes.  The type specification is used to guide the decoding (the
argument to ``make_loads()`` is the type specification we want to construct
from the JSON data)::

  >>> class Example():
  ...     def __init__(self, foo):
  ...         self.foo = foo
  ...     def __repr__(self):
  ...         return '<Example({0})>'.format(self.foo)
  >>> class Container():
  ...     def __init__(self, *examples:[Example]):
  ...         self.examples = examples
  ...     def __repr__(self):
  ...         return '<Container({0})>'.\
		  format(','.join(map(repr, self.examples)))
  >>> loads = make_loads(Cls(Container))
  >>> loads('{"examples": [{"foo":"abc"}, {"foo":"xyz"}]}')
  <Container(<Example(abc)>,<Example(xyz)>)>

Review
~~~~~~

It's possible to see, in outline, how Python's ABCs and type annotations, used
within the Python language (ie. at runtime) could support both product types
and parametric polymorphism.  The work required by a programmer to exploit
these measures directly would be significant, but could be reduced by a
library providing a higher–level interface.

However, many problems remain before this becomes a practical option.

Generator Type Annotations
..........................

Generators do not support type annotations [#]_.  This makes it impossible to
completely specify many types and is particularly damaging for the common case
of standard collections.

.. [#] http://www.python.org/dev/peps/pep-3107/

Interestingly, one suggested solution for annotating generators [#]_ had a
syntax that resembles type-parameterised ABCs (see below).

.. [#] http://mail.python.org/pipermail/python-3000/2006-May/002104.html

Type Annotation Scope
.....................

Some type annotations are impossible due to scoping rules.  For example::

  >>> class Example:
  ...     def method(self, other:Example):
  ...         pass
  NameError: name 'Example' is not defined

SQLAlchemy solves this kind of problem by allowing type names to be strings,
which are later expanded.  I can also imagine situations in which ``self``
would be a useful return type.

ABC Properties
..............

Defining an ABC that includes typed properties, to specify the types of
attributes, is very verbose.  TODO - try this!

Parameterised ABCs with Type Annotations
........................................

The various attributes in an ABC for a ``Sequence``, say, have closely related
types.  This could be expressed as a function, so ``Sequence(int)`` would
generate the ABCs for a sequence of ``int`` values.

Fixing this on an ad–hoc basis does not require any changes to the core
language.  But perhaps a fix to `Type Annotation Scope`_ could also provide a
mechanism to simplify this?

ABC Constructors
................

Since ABCs are, by definition, abstract, they do not support 

DO ABCs DO WHAT I THINK THEY DO? nope.

Incomplete ABCs
...............

Sugar for Properties

Correlated Attribute Types

[Also, class-like products correlate constructor and accessor.  Constructor?!]

How do we get from ``[int]`` to the code outlined in `Typed Collections`_?  We
can use a function, similar to the handling of polymorphism and functors
above.  Perhaps ABCs themselves should be parameterised?  This would codify a
particular relationship between the type annotations of different methods.
The same idea, in more general terms can be phrased as "how should information
be shared between type annotations on a class?"  One answer might be to allow
them access to attributes defined on ``self``.

some other tag that indicates type?  related to constructor args?  could be
library dependent.  that seems to be a problem.  same problem also applies to
type annotations.  suggests that some standard should emerge and be adapted by
the language core.

Typed Objects v Datatypes
.........................

Maybe we need a special datatype for Class(a=..): self.a=... - but isn't that
what named tuples are meant to do?


Sum Types (Alternatives)
........................

For more complete coverage of common structures sum types are needed.  One way
to do this would be to extend the syntax of type annotations to include
alternatives (separated by a comma?).  Another, more exotic, approach might be
possible through an "Amb" operator, adding ambiguity to the language.

Maps and Attributes (Products and Dependent Types)
..................................................

Named tuples too.

Active Type Annotations
.......................

What do they do?

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

Language v Library
..................

Backfitting existing APIs.

Consistency
...........

I understand that Python has grown in an irganic manner, and that this is a
strenght of the language.  I also believe that the cautious, inremental manner
in whch it has been developed has been a benefit.  But still, oh my god, why,
why, why, are there so many inconsistencies and irregularities?  Why are
namedtuples only half implemented?  Why is scope still broken?  Why are type
annotations available only on functions?

Mutable State and Collections
.............................

A flag that indicates change?

Conclusions
-----------

[Check what ABCs actually do]

Embedding — Solves many problems, but makes optimisation hard.

Types are a formalization of the system.  They expose inconsistencies like the
handling of mutable sequences (settitem v hash; iadd on types).

define everything in terms of new abcs + use register.  make the abcs
parametric.  are abcs transitive(sp?)

types increase granularity of abcs to instances.

sumtypes shoudl be less ugly.

Appendix: ``pytyp`` Extensions
------------------------------

Extensions
~~~~~~~~~~

The following features are supported by ``pytyp`` but not discussed in the
text above.

Natural Syntax
..............

``pytyp`` supports the "natural" syntax described above, but the
``normalize()`` function may be necessary when used in contexts that require a
subclass of ``type``::

    >>> isinstance([1,2,3], normalize([int]))
    True
    >>> ininstance([{'a':1, 'b':'two'}], Seq({'a':int, 'b':str})]
    True

The mapping from natural to formal types is flexible, respecting duck typing
as much as possible::

    >>> isinstance([1,'two'], normalize([int, str]))
    True
    >>> fmt(normalize([int, str]))
    'Map(0=int,1=str)'

The ``fmt()`` function is needed because ``__repr__`` on classes is retrieved
from the metaclass, which must be ``ABCMeta`` for inter–operation with
existing classes.

Optional Records
................

Optional records can be specified with a leading double underscore [#]_,
which can be useful mapping between ``dict`` and function parameters (default
values make certain names optional)::

    >>> isinstance({'a':1}, Map(a=int, __b=str))
    True
    >>> isinstance({'a':1, b:'two'}, Map(a=int, __b=str))
    True

.. [#] It's hard to find something that is readable, an aceptable parameter
   name, and unlikely to clash with existing code.

To avoid syntax–related restrictions, ``Map()`` can take a ``dict`` as a
direct argument, via the ``_dict`` parameter, and ``Map.OptKey()`` can mark
optional records::

    >>> isinstance({1:1}, Map(_dict={1:int, Map.OptKey(2):str}))
    True

User–Defined Classes
....................

For user–defined classes we need another level of parameterisation:
``Cls(UserClass)(int, str)`` or, more simply, ``Cls(UserClass, int, str)``
[#]_.

.. [#] The former is appealing, at least on first sight, since it suggests a
   consistent basis for polymorphism — ``Map()`` can be defined as
   ``Cls(Mapping)``, for example — but the details don't work out so well:
   ``Mapping`` is already an ABC, while ``UserClass`` isn't; in the future you
   might hope that ``Map`` and ``Mapping`` would be merged; automating the
   construction of ABCs from concrete classes has no real use in itsef, only
   as a half-way house to polymorphic witnesses.

Structural typing of classes uses attribute names::

    >>> class Foo:
    ...     def __init__(self, x): self.x = x
    >>> isinstance(Foo(1), Cls(Foo, x=int))
    True

Circular References
...................

TODO

Dispatch by Type
................

It's hard to find a convincing example for this [#]_, but since it is easy to
implement::

    >>> Any(a=int, b=str)._on(42,
    ...                       a=lambda _: 'an integer',
    ...                       b=lambda _: 'a string')
    'an integer'

.. [#] ``pytyp`` includes an example with a typed module for a binary tree,
   similar to ML, including dispatch by type.  Like the proverbial dancing
   bear, the amazing thing is not how well it performs, but that it can do so
   at all.

