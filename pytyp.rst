
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

Summary
-------

ABCs [#]_ and type annotations are recent additions to the Python language.
ABCs let programmers describe the kind of data they have in their programs.
Type annotations associate these descriptions with particular variables.
Together these let programmers add type–related metadata to their code and
then use that information, through functions like ``is­inst­ance()`` and
``is­sub­class()``, when the program runs.

This paper describes work to provide more detailed descriptions: instead of
saying "this is a list" you can say "this is a list of integers", for example.
It also describes ways that this information can be used: to check that the
description matches the data, perhaps, or to indicate that different functions
are called depending on the function arguments.

To do all this in a clear, consistent way, I use ideas from "type systems" in
other languages.  But that does not mean that I am adding such a system to
Python; I am simply using the other languages to help decide how best to
describe the data.  The end result stays true to the idea that Python is
"dynamically typed".

.. [#] Abstract Base Classes

-------

**DRAFT / WORK IN PROGRESS - Does NOT correspond to released pytyp library**
(although the latest version at http://www.acooke.org/pytyp.pdf usually
describes the code in the Hg repo at http://code.google.com/p/pytyp/)

:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.16 of 09-05-2011

Abstract
--------

I explore what parametric, polymorphic, algebraic types might "mean" in
Python, present a library that implements one approach, and suggest a few
small changes to the base language as a consequence.

The result is a natural, expressive DSL [#]_, embedded in Python.  Its
semantics extend the ABC approach with registration of instances and nested
iteration over values and types.  The latter allows piecewise verification of
values that cannot be registered.

The approach tries to be "pythonic": it adds type–related metadata to programs
that can be used at run–time; this is optional, and builds on existing
concepts.  As with ABCs, correct use is not enforced by a static type system;
no attempt is made to resolve conflicting specifications.

At the less pythonic extreme, the library also supports method overloading
with dynamic dispatch and type–checking of functions via decorators.

.. [#] Domain Specific Language.

.. contents::
   :depth: 2

Introduction
------------

Some languages have static type systems.  These let the compiler check for
errors before the program is run, but often, in languages like Java, this
seems more of a hinderance than a help.  So many people (like me) prefer
Python to Java because of the freedom associated with a lack of type
declarations.

But other languages — like Haskell and Scala — are using types in more
interesting ways.  And even in Python we sometimes need to use commands like
``isinstance()``, which has some connection with "types".

So there are interesting questions to explore:

#. How do types currently work in Python?  People often talk about classes as
   if they are types; more recently Python has gained the idea of ABCs
   (Abstract Base Classes).  How do they fit together with "duck typing"?

#. Many "modern" uses of types are based on clean, orthogonal ideas.  How do
   these fit with the data structures provided by Python?  How do they fit
   with the existing support for types?

#. What core functions are needed in a library that extends Python's types?
   Instead of saying exactly how to do something, types gives us a way to
   describe what the results should look like.  So how could we extend types
   so that it is easy to use them to write a library that can convert JSON
   data to a given set of Python classes?

Roadmap
~~~~~~~

In the first section, `Current Status`_, I sketch Python's runtime type
support.  This shows how ABCs provide a clear, general model for duck typing.

The next section, `Discussion`_, explores how new ideas can be added to
Python.  For example, the ``Sequence`` ABC, might be extended to
``Sequence(int)`` to describes sequences of integers.  These "parametric ABCs"
could support registration of instances as well as classes; for mutable
containers that do not support hashing (and so cannot be registered)
introspective, structural verification might also be possible [#]_::

    >>> isinstance([1,2,None,4], Sequence(Option(int)))
    True

.. [#] This particular example is not a valid ``pytyp`` specification.  For
   practical reasons (the need to introduce a new metaclass, and the
   difficulty in modfying existing ABCs) the final library uses
   ``Seq(Opt(int))``.

A concete implementation of all this (and more!) is given in `The Pytyp
Library`_ (and `Appendix: Further Details`_).

Finally, in `Conclusions`_, I review the most import lessons from this work.

Terminology
~~~~~~~~~~~

Many terms used to discuss types have meanings related to the static
verification of program properties.  In this paper I am addressing a different
subject.  This means that I will often use the word "type" in a poorly defined
way.  When I need more precision I will use "(static) type system" (about
which one can reliably reason without executing code), "type specification"
(metadata using ABCs to describe Python data), and "duck types" (a model of
runtime behaviour using available attributes).

Current Status
--------------

Python does not have a type system [#]_, but the language does have a notion
of types.

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
attributes.  **Abstract Base Classes (ABCs) resolve this by identifying
collections of attributes, providing a class–like abstraction that is better
suited to duck typing.**

In more detail: a programmer can identify a set of attributes, create an ABC
that contains these, and then either subclass, or call the ``register()``
method, to associate a class with the ABC.  The metaclass for ABCs,
``ABCMeta``, then modifies the behaviour of ``is­inst­ance()`` and
``is­sub­class()`` to expose this relationship at runtime.

It is important to understand that Python does not support the runtime
*verification* of arbitrary duck types [#]_::

  >>> class MyAbc(metaclass=ABCMeta):
  ...     @abstractmethod
  ...     def foo(self): pass
  >>> class MyExample:
  ...     def foo(self): return 42
  >>> issubclass(MyExample, MyAbc)
  False

.. [#] Excepting manual introspection and the "one trick pony" ABCs:
   ``Hashable``, ``Iterable``, ``Iterator``, ``Sized``, ``Container`` and
   ``Callable``.

Instead, ``MyExample`` must either subclass ``MyAbc`` or register itself
(populating a lookup table used by ``isinstance()``).  The ABC acts only as a
marker that signals the veracity of the registered (or subclass) type; it does
not perform a runtime check of the attributes [#]_.

.. [#] This isn't completely true; when used with inheritance it is possible
   for ABCs to define abstract methods, which concrete implementations must
   supply.

Second, Python 3 supports type annotations.  These are metadata associated
with functions [#]_.  For example, the following is syntactically valid::

  def func(a:int, b:str) -> list:
      return [a, b]

.. [#] Python documentation calls them "function annotations", but the use
   cases in PEP3107 all refer to types.

Type annotations are not interpreted or enforced by the language runtime.
They are added to the function metadata and exposed through Python's
``inspect`` package.

When used with ABCs, **type annotations associate variables with type–related
metadata.**

Summary 
~~~~~~~

A consistent, simple, global model of Python's runtime type system exists.  It
is called "duck typing" and, as described above, depends on the availability
of object attributes.

Recent work has started to build on this foundation by reifying collections of
attributes (ABCs) and allowing metdata (formatted in a manner traditionally
associated with types) to be specified on functions.  However, ABCs act only
as an unverified marker; runtime checks are restricted to a few special cases.
Nor are type annotations verified.

So **ABCs are type metadata;** ``isinstance()``, **via** ``ABCMeta``,
**associates type metadata with values; type annotations associate type
metadata with variables.** The rest of this paper builds on this.

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
implicit integer indices: 0,1,2...).

But we have a problem: the step from sequences to maps was more significant
than a simple change of syntax.  **When we try to translate** ``Rec()`` **back
into ABCs with type annotations we find that we need dependent types**.  The
type of the return value from ``__getitem__(key)`` depends on the argument,
``key``.

Nice syntax; shame about the semantics.

Semantics
.........

To improve the semantics we must consider how a type specification is
used.  For example, we might intend to enforce runtime checking of function
arguments, or to specify how data can be transcoded.

On reflection (and experimentation) I can find three broad uses for type
specifications: verification; identification; and expansion.

**Verification** of a value's type (against some declaration) is traditionally
performed by ``isinstance()`` and ``issubclass()``.  ABCs provide a mechanism
for extending these, but need an implementation.  We might examine the value
structurally, comparing it against the type specification piece by piece.
This approach is best suited to "data" types (lists, tuples and dictionaries)
which are used in a polymorphic manner.  Alternatively, we can use the
existing registration and subclass mechanisms, which are more suited to
user–defined classes.

**Identification** of a value's type, although superficially similar to
verfication, is a harder problem.  There is not always a single, well–defined
answer.  In some simpler cases we may have a set of candidate types, in which
case we can verify them in turn, in other cases the instance's class may
inherit from one or more ABCs.  But I don't see a good, "pythonic" solution to
the general problem.

**Iteration** over a value by type covers a variety of uses where we want to
process data in a manner informed by the associated types.  One example is to
automate mapping between ``dict`` and user–defined classes.  Another is
structural type verification.  The handling of ambiguous sum types (see below)
is the most challenging point here.

Setting identification aside, we seem to have two possible semantics: one
based on registration and subclassing of ABCs; the other structural iteration
(similar to catamorphism or "folds").

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

But there are some problems relating this to Python:

* The ``Mapping`` ABC does not include ``tuple`` or ``list``, although these
  can be used as products.

* The ``dict`` class (and ``list``, which can also function as a product) has
  a variable number of entries.  So ``Rec()`` includes a ``__`` argument that
  gives a single type to all "other" values (related to `Optional Records`_,
  described in the Appendix).

* Class attributes can also look like products, but use ``__get­attr__()``
  rather than ``__get­item__()``.  This is described using ``Atr()`` [#]_.  To
  avoid the need to specify all attributes on a class, ``Atr()`` is open to
  additional entries (unlike ``Rec()``, which is closed unless ``__`` is used
  to specify a default type).

.. [#] ``Atr()`` has an advantage over ``Rec()``: it does not require
   dependent types when reduced to ABCs with type annotations because each
   attribute would be described separately and so could have its own type.

So Python appears to have two product types [#]_; one associated with
``__getitem__()``, ``Rec()``; and one with ``__getattr__()``, ``Atr()``.
Neither is closely associated with an existing ABC.

.. [#] In comparison, Javascript's approach to attributes would require only a
   single type.

Sum Types
.........

Although no Python feature maps directly to sum types — a value drawn from a
set of types — there are various related ideas:

* Using ``None`` to indicate a missing value.

* The use of conditional code that either tests types (eg. ``if
  isinstance()``) or that returns mutliple types from a single function.

* Subclassing and method dispatch.

This suggests a relationship between sum types, conditionals and dispatch;
something that will become clearer in ``pytyp``'s support for dynamic
dispatch.  More generally, in a dynamic language like Python, structural
verification of nested sum types will lead to a depth first search with
backtracking when types fail.

I will use notation ``Alt(a=int, b=str)`` to describe sum types below.  The
optional labels might be used for dispatch by type, with a case–like syntax,
for example.

Types as Sets
.............

Types can be considered as [predicates that define] sets of values.  This
suggests two more specifications: ``And()``, which defines a type as the
intersection of its arguments (so ``And(My­Class, Seq(int))`` would be the
instances of ``MyClass`` that are also integer sequences); and ``Or()`` which
is the union.  Other set operations are possible, but don't appear to be very
useful in practice [#]_.

.. [#] An argument could be made for ``Not()``.

``Or()`` is very similar to ``Alt()`` [#]_; the difference is the ability to
name alternatives, which means that ``Alt()`` is not associative, while
``Or()`` is.

.. [#] ``And()`` and ``Or()`` parallel the product and sum types in structural
   verification and so share common ancestors in ``pytyp``.

Note that ``And()`` plays a similar role for type specifications to multiple
inheritance in classes.  Using a combinator rather than inheritance avoids
simplifies the implementation and feels more natural (to me).

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
a syntax to distinguish classes used as types [#]_ and another to allow
dispatch by type (see `Dynamic Dispatch and Iteration`_ below)::

    Ins(c)       # Instances of c
    Sub(c)       # Subclasses of c

.. [#] In ``pytyp`` this use of ``Ins()`` is optional in most cases; bare
   classes in type specifications will be automatically coerced to
   ``Ins(...)``.

Relating the semantics for these type specifications to existing language
features is more difficult.  In particular, **adding type annotations to ABCs
faces significant problems**.  First, it is incomplete: attributes, generators
and named tuples do not support annotations.  Second, dependent types would be
needed to handle ``dict``.  Third, it is verbose, particularly when using
standard container classes which must be subclassed for every distinct use,
but also because it ignores correlations between the types of different
attributes.

Registration with ABCs (or subclassing) is more promising, but cannot handle
all cases, even if extended to include instances; a general solution would
also require a structural (piecewise inspection) approach.

The ``Pytyp`` Library
---------------------

The previous sections explored a variety of ideas.  Now I will describe the
implementation of these ideas within the ``pytyp`` library.  This includes
some rather technical points that arise when embedding a library that
describes a language within the language itself.

ABCs
~~~~

The library takes the "parametric ABC" approach described above.  So, for
example, ``Seq(int)`` is a call to the type sequence constructor ``Seq`` that
returns an ABC representing sequences of integers.  The value of ``Seq(int)``
is a dynamically generated ABC, which is cached in ``Seq`` so that
subsequent calls with the same type argument receive the same instance.

Similarly, ``Ins(X)`` is the type specification for an instance of class
``X``.  Although a type specification can be given in terms of Python classes
(eg. ``Seq(int)``) ``Ins()`` is used to remove any ambiguity.  This is
necessary because type specifications are themselves classes (consider the
difference between ``Seq(int)`` and ``Ins(Seq(int))``: the former represents a
sequence; the latter represents the class ``Seq(int)`` — a type specification
that refers to a type specification).

Construction and Inheritance
............................

Unfortunately, embedding type specifications within the language leads to a
problem [#]_: if the subclass relation is transitive then we cannot reliably
test for the types of type specifications.  Consider the following:

#. ``issubclass(Ins(X), Ins)``
#. ``issubclass(X, Ins(X))``
#. ``issubclass(X, Ins)``

.. [#] This can be seen as a consequence of excluding a conceptual layer
   between classes and instances with a corresponding ``istypespec()``.  The
   approach used here allows easier integration with existing code.

[1] is true because we sometimes need to group parameterised types by "family"
(eg. we need to be able to test whether a sequence of some type is a sequence,
rather than a record).

[2] is true from the meaning of this particular type specification and the
usual relationship between ``isinstance()`` and ``issubclass()`` (eg. both
``isinstance(42, Ins(int))`` and ``issubclass(int, Ins(int))`` are true).

[3] would be true if ``issubclass()`` were transitive.  This is traditionally
the case for any value of ``X``, including ``object`` itself.  But [3] will
cause problems when client code is checking the type of a specification to
dispatch some operation (since everything, apparently, can be a subclass of
``Ins``, how can we detect those type sequences that specify classes?).

In other words, there is a conflict between "is ``X`` a type within the type
specification ``Y``?" and "is ``X`` a type specification of type ``Y``?"

To address this the library has the following structure:

* **Type Specification Constructors** (eg. ``Ins``, ``Seq``) are ordinary
  classes whose ``__new__`` methods act as factories for type specifications.

* **Type Specifications** (eg. ``Ins(X)``, ``Seq()``) are [#]_ dynamically
  created classes, cached in the type constructor by type arguments, that have
  a ``TSMeta`` metaclass.

* **Type Specification Metaclass** (``TSMeta``) is a subclass of ``ABCMeta``
  that extends registration to include instances, adds iteration and
  structural verification, etc.

This isolates the "magic" used to implement [2] (the logic in ``ABCMeta`` and
``TSMeta`` that ``is­instance`` and ``is­sub­class`` delegate to, and which is
extended to make parametric polymorphism possible).

In summary: ``issubclass(X, Ins)`` asks if ``X`` is a subclass of the ``Ins``
constructor; ``issubclass(X, Ins())`` asks if ``X`` is described by the
specification ``Ins()`` [#]_.  The first is resolved using normal Python
subclassing; the second includes modified logic from ``ABCMeta`` and
``TSMeta``.  Since only the latter includes the support for parametric
polymorphism we lose the unwanted transitivity.

.. [#] More exactly, "return".
.. [#] An instance of any class — ``Ins()`` is equivalent to ``Ins(object)`` —
   so the result is ``True``.

This solution does not address the case where a type specification is
subclassed, but those will be proper subclasses that are unlikely to be
confusing during dispatch by type.
   
Class Hierarchy
...............

``Pytyp`` supports all the type specifications discussed earlier.  This is the
full class hierarchy (subclassed or registered to right; ``Se­quence``,
``Container`` and ``Mapping`` are all existing Python ABCs)::

  Product
  +- Sequence
  |  `- Seq -- Seq(*) +- Seq(X)  # Sequences (like [])
  |                   +- X in Sequence.__subclasses__
  |                   `- tuple
  +- Container
  |  `-Rec -- Rec() +- Rec(X)    # Records (like {})
  |                 +- X in Mapping.__subclasses__
  |                 `- tuple
  +- Atr -- Atr(X)               # Attributes (like A.b)
  `- And -- And(X)               # Intersection
                           
  Sum                      
  +- Alt -- Alt(X)               # Alternatives
  |  `- Opt -- Opt(X)            # Optional (or None)
  `- Or -- Or(X)                 # Union

  Ins -- Ins(*) -- Ins(X)        # Instance
  Sub -- Sub(*) -- Sub(X)        # Subclass

None of the ABCs have abstract or mixin methods.  ``Foo(*)`` implies a default
``object`` argument (eg. ``Seq()`` is equivalent to ``Seq(object)``).

Several additional classes modify behaviour.  Classes with ``NoNormalize`` as
an *immediate* superclass are considered to be type specifications during
normalization (other classes will be wrapped by ``Ins()``).  ``NoStructural``
identifies classes that inherit from type specifications and so do not need
structural verification.  Subclasses of ``Atomic`` are displayed without the
``Ins()`` wrapper.

Instance Registration
.....................

``TSMeta`` extends ``__instancecheck__`` (called by ``is­instance()``) to
delegate to ``__instancehook__`` on the class, if present.  This parallels the
use of ``__subclasshook__`` within ``__subclasscheck__`` (the standard ABC
type extension mechanism).

Type specifications extend ABCs with an additional registry, used for
instances.  This is populated by ``register_instance()`` and checked within
``__instancehook__``.

Structural Type Verification
............................

Neither inheritance nor registration will help verify a list of integers,
``[1,2,3]``: subclassing is not useful (``list`` already exists, and anyway we
need this to work at the instance level) and registration fails (the value
cannot be hashed).

In cases like this we must fall back to structural verification: each entry is
checked in turn (the mechanism is described in the next section,
`Iteration`_).  This is inefficient, of course, so the programmer must
consider whether it is appropriate.  The alternative is a custom subclass::

    >>> class IntList(list, Seq(int)): pass
    >>> isinstance(IntList(), Seq(float))
    False

Iteration
~~~~~~~~~

Iteration allows the type specification to guide processing of data.  Each
type specification implements ``_for_each(data, call­back)`` and
``_backtrack(data, call­back)``.  These both pass ``callback`` the current
type specification and a generator that supplies ``(value, spec, name)`` for
each sub–comp­onent of the data.

So, for example, the call ``Seq(int)._for_each([1, 2, 3], callback)`` will
provide ``callback`` with a generator that contains each list entry, in order,
with a ``spec`` of ``int``.  In this case ``name`` will be None, but for
``Rec()``, say, it will name the record.

The callback can recursively call ``_for_each()`` or ``_back­track()`` on
any sub–specifications, allowing the entire data structure to be processed.

Since the behaviour of the callback will usually depend on the type
(otherwise, use Python's more efficient, built–in iteration mechanisms)
``callback`` is an ideal candidate for dyamic dispatch.  See `Appendix:
Further Details`_ for a detailed use case.

The difference between the two routines is how they handle sum types (which
have multiple possible types for a single value).

For Each
........

``_for_each()`` passes ``callback`` each combination of type and value.  For
product types ``callback`` receives each value once, with a type; for sum
types it receives each value multiple times, with a different type each time.

The callback must then handle the two cases appropriately.  For example,
the following code would implement structural type verification::

    def callback(current, vsn):
        if isinstance(current, Product):
	    for (value, spec, name) in vsn:
		if not isinstance(value, spec):
		    return False
	    return True
	else if isinstance(current, Sum):
	    for (value, spec, name) in vsn:
		if isinstance(value, spec):
		    return True
	    return False

I have omitted many details, including the way that this would be called by
``isinstance()``, but you can see how each case is handled separately.

Backtrack
.........

In many cases, iteration over sum types means trying each type in turn until
one works.  For nested sum types this gives a depth first search of the
possibilities.  The ``_backtrack()`` routine makes this explicit: failure is
indicated by raising an exception; the exception is caught and the next
alternative tried.

So with ``_backtrack()``, ``callback()`` receives only a single type for each
value in a sum (other types are tried on alternative calls, if an exception is
raised).  The code for structural type verification becomes::

    def callback(current, vsn):
	for (value, spec, name) in vsn:
	    if not isinstance(value, spec): 
                raise TypeError
	return True

This is simpler than the previous approach because the logic for handling sum
types is moved to ``_backtrack()`` itself (implemented as methods on the
``Sum`` and ``Product`` superclasses).

Examples
~~~~~~~~

The following examples build on the support for types described above to
provide useful functionality.

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
decoding (implemented through nested iteration, as outlined earlier)::

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
registration / subclassing; structural type verification; iteration.

.. [#] Implemented as an embedded, domain–specific language (EDSL).

Registration / subclassing and structural verification are complementary.  The
former allows classes and instances to be registered with, or inherit from,
type specifications.  This gives efficient verification of types.  The latter
is less efficient, but extends verification to mutable containers that cannot
be registered.  If performance is critical users can subclass and extend
existing collections to make more efficient, registered classes.

``Pytyp`` uses type verification to provide function decorators that verifies
arguments and provide dynamic dispatch (similar to multimethods).

Iteration is a general mechanism that recursively explores a value and the
associated type specification.  Type specifications are not part of a
static type system so the concrete type of a value identified with a sum
(ie. ambiguous or alternative) type is unknown; iteration must therefore
support backtracking over the different possible combinations.  This can be
left to the client, or supported within the type library.

``Pytyp`` uses iteration to provide structural verification of types and the
guided conversion of JSON data to Python classes.

Pythonic
~~~~~~~~

The final decision on whether code is "pythonic" can only come from the
community.  And I suspect that they will not, in general, be supportive of the
idea of "adding types" to Python.

However, the work described here does not implement, or advocate, a static
type system.  Instead, it builds on ideas already present in the language
(ABCs, type annotations, ``is­instance()``) to add optional features that
respect the language semantics.  For example, ``Rec(int, str)`` can describe a
``dict`` with keys ``1`` and ``2``, a tuple, a even a list of length 2; no
structure is imposed on the user beyond the attribute–based protocol
(``__getitem__()`` in this case) that already exists in the language.

Open Issues in Python
~~~~~~~~~~~~~~~~~~~~~

Type specifications describe parts of the Python language in a semi–formal
way.  So they highlight inconsistencies.  That specifications are possible at
all implies that Python is already a regularly structured language, but some
irregularities have surfaced and I will describe them below.  They are ordered
by "concreteness".

Type Annotations
................

When developing ``pytyp`` my initial intention was for type specifications to
be syntactic sugar that add type annotations to ABCs.  This would make the
type parameters "readable" to other code.  Instead, the current implementation
stores the parameters in dynamically generated ABCs.

So type annotations are less central to this work than I expected.  This is
largely because **generators — which are particularly important for
collections — do not allow for type annotations**.  This makes it difficult to
extend ABCs with annotations in a consistent way.

The significance of the need for dependent types, when describing ``Rec()``
with ABCs and type annotations, is debatable.  While type specifications are
expressed in the language this may not be a serious problem (dependent types
can be implemented as Python functions), but it might constrain future options
to improve efficiency.

Named Tuples, ABC Granularity
.............................

Named tuples are interesting because they so closely correspond to product
types.  Yet they are "bolted on" to the language and do not support type
annotations.  They also, confusingly, relate a ``Rec()`` over integer keys to
``Atr()``; more useful would be a relationship using the same names (ie. as
between an object and the underlying ``__dict__``; ``pytyp`` provides
``record()`` for this).

A related issue is seen in the granularity of existing ABCs: **there is no
abstraction between** ``Container`` **and** ``Mapping`` / ``Se­quence``
**for** ``__getitem__()`` **and** ``__set­item__()``.  This muddies the
connection between existing ABCs and product types.

Mutability
..........

Mutability of an *individual* value is not specified in the schema outlined.
In practice, Python's ``tuple`` type is immutable and can be used for both
``Seq()`` and ``Rec()`` (integer labels), while ``namedtuple`` also supports
``Atr()``.

Mutability of the *number* of values in a container has more impact on type
specifications because the set of labels must expand with the contents.  Apart
from class attributes (``Atr()``), **Python does not have built–in, mutable
collections of fixed size**.  ``Pytyp`` adds ``record``, similar to
``namedtuple``, to support this.

The inability to register common collection types because they are mutable
(and so cannot be hashed) makes inefficient structural verification of types
necessary.  An efficient, simple way to either "freeze" collections or have
temporary hashes would be very useful [#]_.

.. [#] But, I suspect, impossible to implement efficiently.

More generally, functional programming suggests that accurately tracking
mutability is important, but the runtime information for mutable types in
Python is muddled: ``Sequence`` and ``MutableSequence`` are distinguished by
the *addition* of ``__set­item__()``; the behaviour of mutable structures in
Python depends on the *absence* of ``__hash__()`` and ``__eq__()``.  The
``pytyp`` library emphasises the latter; ``Seq`` is an ugly amalgam of the two
ABCs that switches to structural verification when registration is impossible
(ie. for unhashable instances).

AttributeError is TypeError
...........................

In the context of duck typing, ``AtrributeError`` **should be a subclass of**
``TypeError``.  Or vice–versa?

Open Issues in ``pytyp``
~~~~~~~~~~~~~~~~~~~~~~~~

Efficicency
...........

The issues above also apply to, or affect, ``pytyp``.  In addition, as with
any pure–Python solution, there is a question of efficiency.  For the
occasional type check when debugging this is not an issue, but some of the
features described are unsuitable for use across a Python application
(eg. ubiquitous verification of type annotations).

How could performance be improved if some functionality was moved to the
language run–time?  What would minimal support require?  Perhaps caching would
be simplified by allowing arbitrary tags on (all) values?  Is there a need for
an intermediate conceptual level, between instances and types, that is somehow
related to state?  Are there useful parallels between type verification and
the "unexpected path" handling of a JIT compiler?

Not a Type System
.................

``Pytyp`` **is not a type system; it does not support static reasoning about
program correctness.** It is *only* a library for expressing and interpreting
metadata at run–time.  This fits within the Python ethos, but means, for
example, that inconsistencies and errors are not flagged to the user, nor is
the current type known for a value that has several alternatives (sum types).
The last point implies that **type–guided iteration over data requires
backtracking when inconsistencies are found.**

One way to move ``pytyp`` closer to a type system would be to add type
inference.  This could be a function, called at runtime, that uses type
annotations to connect different type specifications together.  For example,
it could answer questions like "if I call function X with types Y and Z, what
will the type of the result be?"  The additional information Y and Z may help
constrain the type or the result (resolving sum types, for example).

Negative Cache
..............

``ABCMeta`` contains both a register and a negative cache for classes (the
cache contains classes that are know to not be subclasses).  ``TSMeta`` is a
minimal extension of that code, which adds a register for instances, but does
not include a corresponding cache.  It is possible that a more careful
implementation would be more efficienct.

Inheritance, Types as Sets
..........................

**No attempt is made to resolve multiple inheritance of type specifications.**
``And()`` will merge the structural verification, so inheriting from
``And(X,Y)`` is preferable to subclassing both ``X`` and ``Y`` separately
[#]_.

It has already been noted (in `Types as Sets`_) that ``Or()`` is very close in
meaning to ``Alt()``.  Since ``And()`` is similar to inheritance it may be
better to drop both.  This would simplify the library, but make it harder to
use: the DSL approach to describing data is compact and readable; requiring
the user to define new classes instead of writing ``And()`` makes it much more
intrusive.

.. [#] The same logic might be implemented in the ``TSMeta`` metaclass.

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
    >>> normalize([int, str])
    Rec(0=int,1=str)

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

Similarly, a double underscore with no following name indicates a default type
for additional values:

    >>> isinstance({'num':42, 'a':'foo', 'b':'bar'},
    ...            Rec(num=int, __=str))
    True

.. [#] It is hard to find something that is readable, an acceptable parameter
   name, and unlikely to clash with existing code.

To avoid syntax–related restrictions, ``Rec()`` can take a ``dict`` as a
direct argument, via the ``_dict`` parameter.  ``Rec.­Opt­Key()`` can then
mark optional records::

    >>> isinstance({1:1}, 
    ...            Rec(_dict={1:int, Rec.OptKey('b'):str}))
    True

Class and Attributes Shorthand
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Ins()`` constructor provides a shorthand for specifications that include
a class and attributes::

    >>> class Foo:
    ...     def __init__(self, x):
    ...         self.x = x
    >>> isinstance(Foo(1), Ins(Foo, x=int))
    True
    >>> isinstance(Foo('one'), Ins(Foo, x=int))
    False
    >>> Ins(Foo, x=int)
    And(Ins(Foo),Atr(x=int))

Circular References
~~~~~~~~~~~~~~~~~~~

These are defined using ``Delayed()`` which allows references to a type before
it is known::

    >>> d = Delayed()
    >>> d.set(Alt(int, d, str))
    >>> d
    Delayed(Alt(0=int,1=...,2=str))

``isinstance()`` will raise a ``RecursiveType`` exception on recursive
verification of a recursive type (typically this is handled by backtracking in
``Alt()``).

Dynamic Dispatch and Iteration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While developing ``pytyp`` I made various experiments with type dispatch.  The
most readable had the following form::

    >>> sexpr = Delayed()
    >>> sexpr.set(Alt(Seq(sexpr), Any))
    
    >>> class Count:
    ...
    ...     def count(self, vsn):
    ...         (value, spec, _) = vsn
    ...         try:
    ...             return spec._for_each(value, self)
    ...         except TypeError:
    ...             return 1
    ...
    ...     @overload
    ...     def __call__(self, spec, vsn):
    ...         return sum(map(self.count, vsn))
    ...
    ...     @__call__.intercept
    ...     def __call__(self, spec:Sub(Sum), vsn):
    ...         for entry in vsn:
    ...             try:
    ...                 return self.count(entry)
    ...             except TypeError:
    ...                 pass

    >>> sexpr._for_each([1,2,[3,[4,5],6,[7]]], Count())
    7

The ``__call__`` method is marked with the ``overload`` decorator and provides
the default case.  Alternative cases, with the same arguments, but different
type annotations, can then "intercept" the call to that method, to provide
results specific to the restricted argument types.

A better solution for this particular example, however, would use the
backtracking support that ``pytyp`` already provides::

    >>> def count(_, vsn):
    ...     try:
    ...         return sum(s._backtrack(v, count) 
    ...                    for (v, s, _) in vsn)
    ...     except AttributeError:
    ...         return 1
    >>> sexpr._backtrack([1,2,[3,[4,5],6,[7]]], count)
    7

Record
~~~~~~

In a similar manner to ``namedtuple()``, the function ``record()`` constructs
classes that implement both ``Rec()`` and ``Atr()``, providing unified access
to named values.
