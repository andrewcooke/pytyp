
.. role:: raw-math(raw)
    :format: latex html

.. raw:: latex

  \renewcommand{\ttdefault}{txtt}
  \lstset{language=Python,
	  morekeywords=[1]{yield}
  }
  \lstloadlanguages{Python}
  \lstset{
    basicstyle=\small\ttfamily,
    keywordstyle=\bfseries,
    commentstyle=\ttfamily\itshape,
    stringstyle=\slshape,
  }
  \lstset{showstringspaces=false}
  \lstset{columns=fixed,
       basewidth={0.5em,0.4em},
       xleftmargin=-1.5em}
  \inputencoding{utf8}

Algebraic ABCs
==============

**DRAFT - Does not correspond to released pytyp code**

:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.10 of 01-05-2011

Abstract
--------

I explore what parametric, polymorphic, algebraic types might "mean" in
Python, present a library that implements one approach, and suggest a few
small changes to the base language as a consequence.

The result is a natural, expressive DSL [#]_, embedded in Python.  Its
semantics extend the ABC approach with registration of instances and recursion
over values and types.  The latter allows piecewise verification of values
that cannot be registered.

.. [#] Domain Specific Language.

The approach tries to be "pythonic": processing occurs at runtime, is
optional, and builds on existing concepts.  As with ABCs, correct use is not
enforced by a static type system; no attempt is made to resolve conflicting
specifications.

.. contents::
   :depth: 2

Introduction
------------

This paper started as an attempt to answer questions raised by a JSON library
using function annotations.  It took on a life of its own.  When it settled,
eventually, in a consistent approach, I rewrote the library to match.

Roadmap
~~~~~~~

In the first section, `Current Status`_, I sketch Python's runtime type
support.  This shows how ABCs provide a clear, general model for duck typing.

The next section, `Discussion`_, motivated by a need to describe collections
of data, explores how ABCs might include more information.  So the
``Sequence`` ABC, for all sequences, is extended to ``Seq(int)`` (which can
often be abbreviated as ``[int]``), for sequences of integers.  These
"parametric ABCs" support registration of instances as well as classes; for
mutable containers that do not support hashing (and so cannot be registered)
introspective, structural verification is also available::

    >>> isinstance([1,2,None,4], Seq(Opt(int)))
    True
    >>> isinstance({'a':1, 'b':2}, Rec(a=int, b=str))
    False

A concete implementation is given in `The Pytyp Library`_ (and `Appendix:
Further Details`_).

Finally, in `Conclusions`_, I review the most import lessons from this work.

Terminology
~~~~~~~~~~~

Many terms used to discuss types have meanings related to the verification of
program properties.  In this paper I am addressing a different subject.  This
means that I will often use the word "type" in a poorly defined way.  When I
need more precision I will use "(static) type system" (about which one can
reliably reason without executing code), "type specification" (metadata using
ABCs to describe Python data), and "duck types" (a model of runtime behaviour
using available attributes).

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

.. [#] Where it matters, I am discussing only Python 3.

However, the attributes associated with an object are not fixed — it is
possible to modify objects through various mechanisms (including meta-classes
and direct manipulation of the underlying dictionaries) — and the language
runtime does not use the object's class to guide execution [#]_.  Instead,
**each operation succeeds or fails depending on whether any necessary
attribute is present on the instance in question**.

Even so, the notion that an instance's type is its class, and that this
describes how it will behave, is very useful in practice: experienced Python
programmers still describe the behaviour of programs in terms of types and
classes.  This is because Python's extreme flexibility, although useful and
powerful, is rarely exploited to the full.

.. [#] Except for immutable types, which exist partly so that the
   implementation *can* make such an assumption and so operate more
   efficiently.

Duck Typing
~~~~~~~~~~~

Despite the approach outlined above some operations still appear specific to
certain class instances.  For example, the function ``float()`` only works for
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

Recent work extended the language in two interesting ways.

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
  >>> issubclass(MyExample, MyAbc)
  False

.. [#] Except by explicitly checking all attributes through introspection
   or, more usually, by trying an operation and then handling any exception.

Instead, ``MyExample`` must either subclass ``MyAbc`` or register itself
(populating a lookup table used by ``isinstance()``).  **The ABC acts only as
a marker that signals the veracity of the registered (or subclass) type; it
does not perform a runtime check of the attributes [#]_**.

.. [#] This isn't completely true; when used with inheritance it is possible
   for ABCs to define abstract methods, which concrete implementations must
   supply.

Second, Python 3 supports type annotations.  These are metadata associated
with functions [#]_.  For example, the following is valid::

  def func(a:int, b:str) -> list:
      return [a, b]

.. [#] Python documentation calls them "function annotations", but the use
   cases in PEP3107 all refer to types.

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
as an unverified marker; they do not perform any runtime checks.  Nor are type
annotations verified.

Discussion
----------

Typed Collections
~~~~~~~~~~~~~~~~~

To motivate the discussion below consider the following questions.  How do we
define the type of a list of values?  Or a dictionary?

Answering these with tools from the previous section would start with the
appropriate container ABC.  This defines the attributes used to access the
data.  To define the contents we could then add type annotations::

  class IntSequence(Sequence):
      def __getitem__(index) -> int:
          return super().__getitem__(index)
      ...

This has some problems [#]_, but is, I hope, a fair extrapolation of Python's
current approach.

.. [#] It is verbose, particularly when all methods are defined; type
   annotations don't exist for generators
   http://mail.python.org/pipermail/python-3000/2006-May/002103.html; it is
   unclear how to backfit types to an existing API; type annotations are not
   "implemented"; it supports only homogenous sequences (as is normal with
   current type systems).
   
One problem is easy to fix.  We can define a simpler syntax: ``[int]`` or,
more formally, ``Seq(int)``.  I will call this a *type specification*.

This can be extended to inhomogenous collections: dictionaries would look like
``{'a':int, 'b':str}``; tuples like ``(int, str)``.  A unified syntax is
``Rec(a=int, b=str)`` or ``Rec(int, str)`` (where unnamed arguments have
implicit ordered integer indices).

But we have a problem: the step from sequences to maps was more significant
than a simple change of syntax.  **When we try to translate** ``Rec()`` **back
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
in a polymorphic manner.  Alternatively, we can use registration or
subclassing of ABCs, which seems more suited to user–defined classes.

**Identification** of a value's type, although superficially similar to
verfication, is a harder problem.  In some simpler cases we may have a set of
candidate types, in which case we can verify them in turn; in other cases the
instance's class may inherit from one or more ABCs; but I don't see a good,
"pythonic" solution to the general problem.  Perhaps ABCs could pool registry
information?

**Expansion** of a value by type covers a variety of uses where we want to
operate on some subset of the data and, perhaps, recombine the results.  One
example is to automate mapping between ``dict`` and user–defined classes.
Another is structural type verification.

Setting identification aside, we seem to have two possible semantics: one
based on registration and subclassing of ABCs; the other structural.

A Little Formality
~~~~~~~~~~~~~~~~~~

I will now explore how type specifications are related to various concepts
from type theory.  The aim here is not to directly emulate other languages,
but to use common patterns to structure our approach.

Parametric Polymorphism
.......................

Since we started with data structures we have already addressed this:
``Seq(x)`` is polymorphic in ``x``, for example.  However, it is worth drawing
attention to an important point: **polymorphism occurs naturally in Python
data structures at the level of instances, not classes**.  This contrasts with
the current use of ABCs, which is at the class level.

So the idea that ``isinstance([1,2,3], Seq(int))`` evaluates as ``True``
implies a significant change to the language semantics: ``isinstance()``
would depend on the *state* of an instance as well as its class.  The
relationship between ``isinst­ance()`` and ``issubclass()`` would shift: the
former could no longer be expressed in terms of the latter (alone).

Product Types
.............

The handling of maps above (``Rec(a=int, b=str)``) is close to the concept of
product types: a record with a fixed number of values (referenced by label or
index), each with a distinct type.

But there are three problems relating this to Python:

#. The ``Mapping`` ABC does not include tuples.  Instead, ``Rec()`` is defined
   only in terms of ``__getitem__()`` and ``__setitem__()``.

#. The ``dict`` class (and ``list``, which can also function as a product) has
   a variable number of entries.  So ``Rec()`` includes a ``__`` argument that
   gives a single type to all "other" values (related to `Optional Records`_,
   described in the Appendix).

#. Class attributes can also look like products, but use ``__getattr__()``
   rather than ``__getitem__``.  This is described using ``Atr()`` [#]_.

.. [#] ``Atr()`` has an advantage over ``Rec()``: it does not require
   dependent types when reduced to ABCs with type annotations because each
   attribute would be described separately and so could have its own type.

So Python appears to have two product types; one associated with
``__getitem__()`` (``Rec()``); and one with ``__getattr__()`` (``Atr()``).  In
comparison, Javascript's approach to attributes would require only a single
type.

Sum Types
.........

The only Python feature I can find that is related to sum types is the idea
that ``None`` indicates a missing value, similar to the ``Maybe`` type.

If we need this concept we can use the notation ``Alt(a=int, b=str)`` (the
optional labels might be used for dispatch by type, with a case–like syntax,
for example).

Types as Sets
.............

Types can be considered as [predicates that define] sets of values.  This
suggests two more specifications: ``And()``, which defines a type as the
intersection of its arguments (so ``And(My­Class, Seq(int))`` would be the
instances of ``MyClass`` that are also integer sequences); and ``Or()`` which
is the union.  Other set operations are possible, but don't appear to be very
useful in practice [#]_.

.. [#] An argument could be made for ``Not()``.

``Or()`` is very similar to ``Alt()`` [#]_: the difference is the ability to
name alternatives, which means that ``Alt()`` is not associative, while
``Or()`` is.

.. [#] ``And()`` and ``Or()`` parallel the product and sum types in structural
   verification and so share common ancestors in ``pytyp``.

Note that ``And()`` plays a similar role for type specifications to multiple
inheritance in classes.  This is discussed below in `Inheritance,
Inconsistencies`_.

Summary
~~~~~~~

This section introduced a syntax that can describe polymorphic, algebraic data
types (roughly translated into Python's runtime context) within Python code,
largely at the instance level::

    Seq(a)       # Sequences of type a
    
    # products
    Rec(a,b,...) # Type a x b x ... via __getitem__ or []
    Atr(a,b,...) # Type a x b x ... via __getattr__ or .
    
    # sums
    Alt(a,b,...) # Type a + b + ...
    Opt(a)       # Alias of Alt(value=a,none=type(None))

    # sets
    And(a,b,...) # Type a n b n ... (intersection)
    Or(a,b,...)  # Type a u b u ... (union)

In addition, because the specifications above are built using classes, we need
a syntax to distinguish classes used as types [#]_::

    Cls(c)       # Subclasses of c

.. [#] In ``pytyp`` this is optional unless referring to the class of a type
   operator; immutable types like ``int`` and ``str`` are not converted by
   ``normalize()``.

Relating the semantics for these type specifications to existing language
features is more difficult.  In particular, adding type annotations to ABCs
faces significant problems.  First, it is incomplete: attributes, generators
and named tuples do not support annotations.  Second, dependent types would be
needed to handle ``dict``.  Third, it is verbose, particularly when using
standard container classes which must be subclassed for every distinct use,
but also because it ignores correlations between the types of different
attributes.

Registration with ABCs (or subclassing) is more promising, but cannot handle
all cases, even if extended to include instances; a general solution would
also require a structural (piecewise inspection) approach.

In fact, the **structural inspection and registration / subclassing are
complementary**: the traditional ABC approach would work well for user-defined
classes; structural verification would be better suited to the built–in
container types.  There would be a trade–off between convenience and speed:
where necessary built–in containers could be replaced by immutable, registered
custom classes.

The ``Pytyp`` Library
---------------------

Approach
~~~~~~~~

The previous sections explored a variety of ideas.  Now I will describe the
``pytyp`` library.  This supports two general uses, identified in `Semantics`_
above: verification and expansion.

Two approaches to verification have been discussed: registering with ABCs is
efficient, but restricted to hashable instances; a structural approach allows the
library to also work with Python's common, mutable data structures.  ``Pytyp``
supports both.

ABCs
~~~~

We add parametric polymorphism by creating subclasses to contain the extra
type information.  So, hypothetically, ``Sequence(int)`` would create (or
retrieve from a cache, if it already exists) a subclass of the existing ABC
``Sequence``, parameterised by ``int``, which would support both subclassing
and registration.

Class Hierarchy
...............

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

Also, ``Record`` and ``MutableRecord`` are introduced as subclasses of
``Collection``, adding ``__getitem__()`` and ``__set­item__()``, respectively.
``Sequence``, ``Rec``, etc. are then registered with these.

Registration
............

We must extend registration to include instances.  This implies an extra cache
in the ABCs and a modification to the code that implements ``isinstance()``.

Extending ``isinstance()`` is difficult: despite the language in PEP 3119 [#]_
and Issue 1708353 [#]_, ``__instancecheck__()`` can only be over–ridden *on
the metaclass* [#]_.  Since a new metaclass would break inheritance of the
existing ABCs ``pytyp`` uses a "monkey patch" to delegate to
``__inst­ance­hook__()`` [#]_ on the class, if defined.

With this in place, registration works as expected::

    >>> Seq(int).register_instance(random_object)
    >>> isinstance(random_object, Seq(int))
    True
    >>> isinstance(random_object, Seq(float))
    False

.. [#] http://www.python.org/dev/peps/pep-3119/
.. [#] http://bugs.python.org/issue1708353
.. [#] http://docs.python.org/reference/datamodel.html#customizing-instance-and-subclass-checks
.. [#] Named to resemble ``__subclasshook__()``, used for ``issubclass()`` 
   which *is* already supported (as noted earlier, before this work the two
   were largely equivalent).

Structural Type Verification
............................

Unfortunately, neither approach above will help with a list of integers,
``[1,2,3]``.  Subclassing is not useful (``list`` already exists, and anyway
we need this to work at the instance level) and registration fails (the value
cannot be hashed).

In cases like this we must fall back to structural verification: each entry is
checked in turn.  This is inefficient, of course, so the programmer must
consider whether it is appropriate::

    >>> isinstance([1,2,3], Seq(int))
    True

Note that structural type verification is disabled if the class inherits from
a polymorphic ABC.  This is to avoid confusing results with empty containers.
For example the following would have returned true if structural typing had
been invoked::

    >>> class MyIntList(list, Seq(int)): pass
    >>> isinstance(MyIntList(), Seq(float))
    False

Expansion
~~~~~~~~~

Expansion is the recursive exploration of data described by a type
specification.  A callback allows values to be processed (it receives value,
type specification, and any available label) and can recurse on its contents,
giving the caller control over exactly what values are "atomic".  Exceptions
are made available to the callback by providing the data as generators.

This is used to implement structural type verification: each value in turn is
checked against the ABC registry and superclasses; if these fail then the
value is expanded and the process repeated on the contents.

Examples
~~~~~~~~

Type Verification
.................

The ``checked`` decorator verifies parameters and return values against the
specification in the type annotation::

  >>> @checked
  ... def int_list_len(s:[int]) -> int:
  ...     return len(s)
  >>> int_list_len([1,2,3])
  3
  >>> int_list_len('abc')
  Traceback (most recent call last):
    ...
  TypeError: Type Seq(int) inconsistent with 'abc'.

JSON Decoding
.............

Here JSON data, expressed using generic data–structures, are decoded into
Python classes.  Type specifications — in the call to ``make_loads()`` and via
an annotation on the ``Container()`` constructor — are used to guide the
decoding (implemented through recursive expansion, as outlined earlier)::

  >>> class Example():
  ...     def __init__(self, foo):
  ...         self.foo = foo
  ...     def __repr__(self):
  ...         return '<Example({0})>'.format(self.foo)
  >>> class Container():
  ...     def __init__(self, *examples:[Example]):
  ...         self.examples = examples
  ...     def __repr__(self):
  ...         return '<Container({0})>'.format(
  ...             ','.join(map(repr, self.examples)))
  >>> loads = make_loads(Container)
  >>> loads('{"examples": '
  ...         '[{"foo":"abc"}, {"foo":"xyz"}]}')
  <Container(<Example(abc)>,<Example(xyz)>)>

Conclusions
-----------

I have shown how type specifications — metadata using parameterised ABCs to
describe Python data at the class and instance level — can be expressed within
Python [#]_.  I have also provided an implementation with three operations:
registration / subclassing; structural type verification; expansion.

.. [#] Implemented as an embedded, domain–specific language (EDSL).

Registration / subclassing and structural verification are complementary.  The
former allows classes and instances to be registered with, or inherit from,
type specifications.  This gives efficient verification of types.  The latter
is less efficient, but extends verification to mutable containers that cannot
be registered.  If performance is critical users can subclass and extend
existing collections to make more efficient, registered classes.

Expansion is a general mechanism that recursively explores a value and the
associated type specification.  In ``pytyp`` it is used to implement
structural verification and the guided conversion of JSON data to Python
classes.

Pythonic
~~~~~~~~

The final decision on whether code is "pythonic" can only come from the
community.  And I suspect that they will not, in general, be supportive of the
idea of "adding types" to Python.

However, the work described here does not implement, or advocate, a static
type system.  Instead, it builds on ideas already present in the language
(ABCs, type annotations, ``is­instance()``) to add optional features that
respect the language semantics.  For example, ``Rec(int, str)`` can describe a
tuple, a two value list, or even a ``dict`` with keys ``1`` and ``2``; no
structure is imposed on the user beyond the attribute–based protocol
(``__getitem__()`` in this case) that already exists in the language.

Open Issues in Python
~~~~~~~~~~~~~~~~~~~~~

Type specifications describe parts of the Python language in a semi–formal
way.  So they highlight inconsistencies.  That specifications are possible at
all implies that Python is already a regularly structured language, but some
irregularities have surfaced and I will describe them below.  They are ordered
by "concreteness".

isinstance() v issubclass()
...........................

The ABC machinery for ``issubclass()`` includes ``__sub­class­hook__()``.
Unfortunately there is no corresponding ``__inst­ance­hook__()`` for
``isinstance()``.  This is significant because type polymorphism in Python
often occurs at the instance level: ``pytyp`` has to add the hook by monkey
patching ``ABCMeta``.

Type Annotations
................

Type annotations are less central to this work than I expected.  Generators
are an important part of Python — particularly for container types where
polymorphism is most applicable — so the lack of associated metadata makes it
difficult to extend ABCs with annotations in a consistent way.

The significance of the need for dependent types, when describing ``Rec()``
with ABCs and type annotations, is debatable.  While type specifications are
expressed in the language, it is not a big deal, but it might constrain future
options to improve efficiency.

Named Tuples
............

Named tuples are interesting because they so closely correspond to product
types.  Yet they are "bolted on" to the language and do not support type
annotations.  They also, confusingly, relate a ``Rec()`` over integer keys to
one over names; more useful would be a relationship between ``Rec()`` and
``Atr()`` using the same names — ``pytyp`` provides ``record()`` for this.

ABC Granularity
...............

This is a known, hard problem, but it is surprising to find no abstraction
between ``Container`` and ``Mapping`` / ``Se­quence`` for ``__getitem__()``
and ``__set­item__()``.  ``Pytyp`` adds the ``Record`` ABC here.

Mutability
..........

Mutability of an *individual* value is not specified in the schema outlined.
In practice, Python's ``tuple`` type is immutable and can be used for both
``Seq()`` and ``Rec()`` (integer labels), while ``namedtuple`` also supports
``Atr()``.

Mutability of the *number* of values in a container has more impact on type
specifications because the set of labels must expand with the contents.  Apart
from class attributes (``Atr()``), Python does not have built–in, mutable
collections of fixed size.  ``Pytyp`` adds ``record``, similar to
``namedtuple``, to support this.

More generally, functional programming suggests that accurately tracking
mutability is important, but the runtime information for mutable types in
Python is muddled: ``Sequence`` and ``MutableSequence`` are distinguished by
the *addition* of ``__set­item__()``; the behaviour of mutable structures in
Python depends on the *absence* of ``__hash__()`` and ``__eq__()``.  The
``pytyp`` library emphasises the latter; ``Seq`` is an ugly amalgam of the two
ABCs that switches to structural verification when registration is impossible
(ie. for unhashable instances).

Perhaps a mechanism to "seal" collections (or a flag that indicates that they
have been mutated; that the seal is broken) would allow universal hashing?
Implemented using weak references?  I don't have a useful, workable suggestion
here, but something feels wrong.

Expansion Through Metaclasses
.............................

Metaclasses are very powerful, but they are difficult to extend when "frozen
in" to the existing class hierarchy (ie. if you replace ABCMeta you have to
re–implement at least the ``abc`` package).  This would be less of an issue if
metaclasses could be over–ridden at the class level.  But, just as instances
cannot over–ride special methods on classes, classes cannot over–ride special
methods on metaclasses.  I appreciate the regularity of this approach, but the
behaviour of instances and classes is largely motivated (I believe?) through
efficiency; do classes and metaclasses need the same restrictions?

Open Issues in ``pytyp``
~~~~~~~~~~~~~~~~~~~~~~~~

The issues above also apply to, or affect, ``pytyp``.  In addition, as with
any pure–Python solution, there is a question of efficiency.  For the
occasional type check when debugging this is not an issue, but some of the
features described are unsuitable for use across a Python application
(eg. ubiquitous verification of type annotations).

CHECK AND BE EXPLICIT ABOUT ERROR.

How could performance be improved if some functionality was moved to the
implementation?  What would minimal support require?  Perhaps caching would be
simplified by allowing arbitrary tags on (all) values?  Is there a need for an
intermediate conceptual level, between instances and types, that is somehow
related to state?  Are there useful parallels between type verification and
the "unexpected path" handling of a JIT compiler?

Inheritance, Inconsistencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No attempt is made to resolve multiple inheritance of type specifications.
``And()`` will merge the structural verification, so inheriting from
``And(X,Y)`` is preferable to ``X`` and ``Y`` separately [#]_.

.. [#] The same logic might be implemented in a metaclass; see `Expansion
   Through Metaclasses`_.

More generally, it is quite possible (as with ABCs) to specify contradictory
types.  So don't do that.

Functions
.........

``Pytyp`` was motivated by data processing and type specifications do not
include functions.

In applications where functions are used — for example, in the constructors of
classes when mapping from JSON to Python — it has been sufficient to place
type specifications in the annotations.

So the `JSON Decoding`_ example above uses the annotation::

    def __init__(self, *examples:[Example]):

which is found by intrsopection on ``Con­tainer``, passed to
``make­_loads()``, rather than, say::

    loads = make_loads(And(Container, 
                   Fun(__init__, examples=[Example])))

A distributed approach using type annotations is natural and compact here, but
may not be suitable in all cases.

Acknowledgments
---------------

Thanks to Matthew Willson for useful comments.

Appendix: Further Details
-------------------------

Abbreviations and Normalisation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Pytyp`` supports the "abbreviated" syntax described above, but the
``normalize()`` function may be necessary when used in contexts that require a
subclass of ``type``::

    >>> isinstance([1,2,3], normalize([int]))
    True
    >>> isinstance([{'a':1, 'b':'two'}], 
    ...            Seq({'a':int, 'b':str}))
    True
    >>> fmt(normalize([int, str]))
    'Rec(0=int,1=str)'

The ``fmt()`` function is needed because ``__repr__`` on classes is retrieved
from the metaclass, which must be ``ABCMeta`` for inter–operation with
existing classes.

Optional Records
~~~~~~~~~~~~~~~~

Optional records can be specified with a leading double under­score [#]_,
which can be useful mapping between ``dict`` and function parameters (default
values make certain names optional)::

    >>> isinstance({'a':1}, Rec(a=int, __b=str))
    True
    >>> isinstance({'a':1, 'b':'two'}, 
    ...            Rec(a=int, __b=str))
    True

.. [#] It is hard to find something that is readable, an aceptable parameter
   name, and unlikely to clash with existing code.

To avoid syntax–related restrictions, ``Rec()`` can take a ``dict`` as a
direct argument, via the ``_dict`` parameter, and then ``Rec.­Opt­Key()`` can
mark optional records::

    >>> isinstance({1:1}, 
    ...            Rec(_dict={1:int, Rec.OptKey(2):str}))
    True

Class Shorthand
~~~~~~~~~~~~~~~

The ``Cls()`` constructor provides a shorthand for specifications that include
a class and attributes::

    >>> class Foo:
    ...     def __init__(self, x):
    ...         self.x = x
    >>> isinstance(Foo(1), Cls(Foo, x=int))
    True
    >>> isinstance(Foo('one'), Cls(Foo, x=int))
    False
    >>> fmt(Cls(Foo, x=int))
    'And(Cls(Foo),Atr(x=int))'

Circular References
~~~~~~~~~~~~~~~~~~~

These are defined using ``Delayed()`` which allows references to a type before
it is known::

    >>> d = Delayed()
    >>> d.set(Alt(int, d, str))
    >>> fmt(d)
    'Delayed(Alt(0=int,1=...,2=str))'

``isinstance()`` will raise ``RecursiveType`` exception on recursive
verification of a recursive type (typically this is handled by ``Alt()`` which
will attempt another alternative).

Dispatch by Type
~~~~~~~~~~~~~~~~

I don't have a convincing example for this [#]_, but since it is easy to
implement::

    >>> Alt(a=int, b=str)._on(42,
    ...                       a=lambda _: 'an integer',
    ...                       b=lambda _: 'a string')
    'an integer'

.. [#] ``Pytyp`` includes an example with a typed module for a binary tree,
   similar to ML, including dispatch by type.  Like the proverbial dancing
   bear, the amazing thing is not how well it performs, but that it can do so
   at all.

Record
~~~~~~

In a similar manner to ``namedtuple()``, the function ``record()`` constructs
classes that implement both ``Rec()`` and ``Atr()``, providing unified access
to named values.
