
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


Possible Runtime Uses of Metadata (Vaguely) Related to Tagged Values
====================================================================

:Subtitle: Exploring Types in Python
:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.3 of 17-04-2011

Abstract
--------

To do.

.. contents::
   :depth: 3

Introduction
------------

Context
~~~~~~~

This paper was motivated by the development of a Python package called
``pytyp``, intended to improve JSON inter-operability, which started with an
approach that, below, I have called "(structural) expansion".

I soon realised that the type–related code could be more general, extracted it
into a separate module, and added support for verification of type
annotations.  At this point I also started writing this paper, partly as
documentation and partly to record my internal dialogue about how types should
be used in Python.

The paper clarified, for me, the role of witness typing (see `Recent
Extensions`_ below) and led me to revise and extend my library.  The two then
grew symbiotically: ``pytyp`` tests my ideas; the paper records the reasons
for my decisions and opens new avenues to explore.

[More here once done]

Roadmap
~~~~~~~

In the first section, `Current Status`_, I sketch the runtime type support
that exists in Python.  This shows how ABCs provide a clear, general model for
duck typing.

`A Pythonic Extension`_ extrapolates from that to explore possible future
developments.  The first few sub-sections are speculative (with some concrete
`Examples`_); the issues raised are then revised and clarified in `Review`_.

[Needs fixing once done]

Terminology
~~~~~~~~~~~

Many terms related to types have specific meanings related to the verification
of program properties.  In this paper I am addressing a different subject
[#]_.  This means that I will often use the word "type" in a poorly defined
way.  When I need more precision I will use "(static) type system" (about
which one can reliably reason without executing code), "type specification"
(metadata describing Python classes and ABCs), and "duck types" (explained
below; a model of runtime behaviour using available attributes).

.. [#] See title.  In the section `A Little Formality`_ I discuss how type
   systems can guide type specifications.

Current Status
--------------

Python does not have a static type system [#]_, but the language does have a
notion of types.

.. [#] In the sense defined in `Terminology`_.

Classes and Attributes
~~~~~~~~~~~~~~~~~~~~~~

The principal abstraction for structuring source code is ``class``.  This
specifies a set of attributes (directly and through inheritance) for class
instances (objects).  The class associated with an object is universally
referred to as its type and available at runtime via the ``type()`` function.

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

Work related to Python 3 extended the language in two interesting ways.

First, it addressed the conflict described above, which still exists in
theory, even if it is rarely important in practice: on the one hand,
programmers behave as though Python's runtime behaviour can be reliably
explained in terms of types; on the other, the runtime functions in terms of
available attributes.  Abstract Base Classes (ABCs) resolve this contradiction
by identifying collections of attributes, providing a class–like abstraction
that is better suited to duck typing.

However, Python still does not support the runtime verification of arbitrary
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
(populating a lookup table used by ``isinstance()``).  I will call this
approach "witness typing" since **the ABC acts only as a witness to the
veracity of the registered (or subclass) type; it does not perform a runtime
check of the attributes** [#]_.

.. [#] No connection with witness types in Haskell is implied, although the
   idea is loosely related.

Second, Python 3 supports (but does enforce) type annotations.  These are
metadata associated with functions [#]_.  For example, the following is
valid::

  def func(a: int, b:str) -> list:
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
as a witness to types; they do not perform any runtime checks.

A Pythonic Extension
--------------------

Typed Collections
~~~~~~~~~~~~~~~~~

Syntax
......

To motivate our exploration consider the following questions.  How do we
define the type of a list of values?  Or a dictionary?  What if the contents
are drawn from an inhomogenous set of types?

Answering these with tools from the previous section would start with the
appropriate container ABC.  This defines the attributes used to access the
data (ie that we have suitable methods to treat the container as a list, or a
dictionary — more correctly, as a ``Sequence`` or ``Mapping``, which are ABCs
defined in the ``collections`` package).  To define the contents we must also
use type annotations::

  class IntSequence(Sequence):
      def __next__() -> int:
          return super(IntSequence, self).__next__()
      ...

This has some problems [#]_, but is, I hope, a fair extrapolation of Python's
current approach.  One problem is easy to fix: we can define a simpler syntax:
``[int]`` or, more formally, ``Seq(int)`` [#]_.  I will call this a *type
specification*.

.. [#] It is verbose, particularly when all methods are defined; type
   annotations don't exist for generators
   http://mail.python.org/pipermail/python-3000/2006-May/002103.html; it's
   unclear how to backfit types to an existing API; type annotations are not
   "implemented"; as is normal with current type systems it supports only
   homogenous sequences)
   
.. [#] The ``normalize()`` function in ``pytyp`` will convert the first
   expression to the second, but there is little reason to do so unless
   ``pytyp`` is extended to include literal values (the distinction between
   values and types becomes important — we might be referring to a value
   that is a list containing a single value, which happens to be ``int``).

This "natural" syntax can be extended to inhomogenous collections:
dictionaries look like ``{'a':int, 'b':str}``; tuples look like ``(int,
str)``.  But these representations appear tied to specific classes, rather
than the ``Mapping`` ABC (of which both ``dict`` and ``tuple`` are
subclasses).  A better syntax would be ``Map(a=int, b=str)`` or ``Map(int,
str)`` (where integer indices are implicit).
   
The step from sequences to maps is more significant than a simple change of
syntax.  **When we try to translate** ``Map()`` **back into ABCs with type
annotations we find that we need dependent types** (the type of the return
value from ``__getitem__(key)`` depends on the argument, ``key``).  This is a
consequence of Python using a parametric interface to access records, so it
will not apply to attribute access on objects.

Semantics
.........

Given a type specification, what does it "mean"?  The answer depends on its
use.  For example, we might intend to enforce runtime checking of function
arguments, or to specify how data can be decoded (see below for code).

On reflection I can find three broad uses for types: verification;
identification; and expansion.

**Verification** of a value's type (against some declaration) can be performed
in various ways.  We might examine the value structurally, comparing it
against the type specification piece by piece.  This approach seems best
suited to "data" types (lists, tuples and dictionaries) which tend to be used
in a polymorphic manner [#]_.  Alternatively, we can use witness typing,
extended to include types, which seems more suited to user–defined classes.

.. [#] Assuming that the computational cost is not prohibitive.

That ``isinstance([1,2,3], Seq(int))`` should return ``True`` is intuitive,
but implies a significant change to the language semantics — ``isinstance()``
now depends on the state of an instance as well as its class.

In other words, the relationship between ``isinstance()`` and ``issubclass()``
has changed.  Before, the former could be expressed in terms of the latter.
This is not true when ``isinstance()`` is concerned with instance state.

**Identification** of a value's type, although superficially similar to
verfication, is a harder problem.  In some simpler cases we may have a set of
candidate types, in which case we can verify them in turn; in other cases the
instance's class may inherit from one or more ABCs (this would still need
extending to include type information); but I don't see a good, "pythonic"
solution to the general problem.  Perhaps type witnesses (ABCs extended to
include type information) could pool registry information?

**Expansion** of a value by type covers a variety of uses where we want to
operate on some sub-set of the data and, perhaps, recombine the results into a
similar structure to before.  One example is the decoding of JSON values by
``pytyp`` (see example below).  Another is structural type verification.

A Little Formality
~~~~~~~~~~~~~~~~~~

I will now explore how type specifications fit within three core concepts of
type theory: parametric polymorphism; product types; and sum types.

Polymorphism
............

Since we started with data structurs we have already addressed this point:
``Seq(x)`` is polymorphic in ``x``, for example.  However, it's worth drawing
attention to an important point, that **polymorphism occurs naturally in
Python data structures at the level of instances, not classes**.  This
contrasts with the current implementation of witness typing, ABCs, which is at
the class level, and explains the need to introduce a (clumsy) extra class,
``IntSequence``, in the opening example.

If we assume that the type system is inclusive (that subclasses can substitute
for classes) then unbounded polymorphism can be specified using ``object``.
For example ``Seq(object)`` is a sequence of any value [#]_.

.. [#] In ``pytyp`` this has the shorthand ``...`` (ellipsis, a singleton
   intended for use in array access, but available generally in Python 3's
   grammar).

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

This has one significant advantage over ``Map()``: it does not require
dependent types when reduced to ABCs.  This is because each attribute would be
described separately, and so could have its own type.  It also has a
disadvantage: in the reduction to ABCs type annotations in the constructor
[#]_ are related to type annotations for the properties.

And isn't this familiar?  It's very like named tuples.  Except that they are
second class citizens that don't directly support type annotations...

.. [#] The alert reader may ask what a constructor is doing in an ABC.  This
   is discussed in the `Review`_ below.

Sum Types
.........

Python does not have a natural encoding of sum types (alternatives).  This is
not too surprising — sum types are used for *variables* rather than *values*
and historically Python's notion of types has focused on the latter [#]_.

.. [#] As stated near the start of the paper, Python lacks a (static) type
   system.

If we need this concept we can use the notation ``Alt(a=int, b=str)`` (the
optional labels might be used for dispatch by type, with a case–like syntax,
for example).

Python does have a common idiom for the most popular sum type, "Maybe":
missing values are represented by ``None``.  We could express this for
integers as ``Alt(none=None, value=int)`` [#]_.

.. [#] ``pytyp`` has the abbreviation ``Opt()`` for this.

Implementation
~~~~~~~~~~~~~~

Approach
........

The previous sections have explored a variety of ideas.  Now we will consider
an implementation.  This will support two general uses, identified in
`Semantics`_ above: verification and expansion.

Two possible approaches for verification were discussed above.  One was
through expansion, which we can use as a test for the more general expansion
support.  The other required an extension to witness typing.

The most obvious way to extend witness typing was used at the start of this
paper — adding type annotations to ABCs — but has several problems.  First, it
is incomplete: attributes and generators do not support annotations, and scope
issues complicate some common uses.  Second, dependent types would be needed
to handle ``dict``.  Third, it is verbose, particularly when using the
standard container classes, which must to be subclassed for every distinct
use, but also because it ignores correlations between the types of different
attributes.  Fourth, it is misleading (as are current ABCs) in that it
emphasises details that are not verified by the witness–based implementation.

Instead, I will focus on a registration–based approach.  This will extend the
ABC ``register()`` method with parameters to indicate polymorphism, the
ability to register instances, and a fallback to a structural approach when
needed.

Library Structure
.................

Existing ABCs can be used in two ways: via inheritance or by registration.  We
can preserve this while adding polymorphism by subclassing, to give a new
class where we can add functionality, and then intercepting *direct* calls to
the constructor to create another level of witnesses, specific to a particular
type specification [#]_.

.. [#] See ``pytyp`` source for full details.

So, for example, ``Seq`` subclasses ``Sequence`` and ``Seq(Int)`` creates a
subclass of ``Seq`` specialised to represent ``int`` sequences, which can
itself be either subclassed or used for registration::

    >>> class MyIntList(list, Seq(int)): pass
    >>> isinstance(MyIntList(), Seq(int))
    True
    >>> isinstance(MyIntList(), Seq)
    True
    >>> isinstance(MyIntList(), Sequence)
    True
    >>> isinstance(MyIntList(), Seq(float))
    False
    >>> Seq(int).register_instance(random_object)
    >>> isinstance(random_object, Seq(int))
    True

The ``Seq`` level is needed only to add extra functionality to the existing
classes; it could be removed if support for polymorphism was added directly to
the core language.

Expansion
.........

Expansion can be implemented as a recursive exploration of the graph implicit
in the type specification.  Callbacks allow values to be processed; these can
recurse on their contents, giving the caller control over exactly what values
are "atomic".  An additional callback could handle errors, in case the caller
intends to use these to coerce or otherwise process the data.

Care will be needed to handle loops gracefully.

Extensibility?  (Cls)

Verification
............

To add witness typing to the `Library Structure`_ described above we must
override the instance check to include the new registry.  This is more
difficult than it appears: despite the language in PEP 3119 [#]_ and Issue
1708353 [#]_, ``__instancecheck__()`` can only be overrriden *on the
metaclass* [#]_.  Since providing a new metaclass would break inheritance of
the existing ABCs ``pytyp`` uses a "monkey patch" to delegate to
``__cls_instancecheck__()`` on the class, if defined.

.. [#] http://www.python.org/dev/peps/pep-3119/
.. [#] http://bugs.python.org/issue1708353
.. [#] http://docs.python.org/reference/datamodel.html#customizing-instance-and-subclass-checks

For user–defined classes we need another level — ``Cls(UserClass)(int, str)``
or, more simply, ``Cls(UserClass, int, str)`` [#]_.

.. [#] The former is appealing, at least on first sight, since it suggests a
   consistent basis for polymorphism — ``Map()`` can be defined as
   ``Cls(Mapping)``, for example — but the details don't work out so well:
   ``Mapping`` is already an ABC, while ``UserClass`` isn't; in the future you
   might hope that ``Map`` and ``Mapping`` would be merged; automating the
   construction of ABCs from concrete classes has no real use in itsef, only
   as a half-way house to polymorphic witnesses.

Finally, there is an issue related to mutability: should it be possible to
register classes that cannot be hashed?  A pythonic approach would say no,
even though I personally think this could be useful (the alternative, using
structural verification of each entry, is expensive for lists).  One
resolution might be an extension to mutable containers that allow changes to
be detected.

Mutability
..........

setitem v hash.

Extensibility
.............

The ``pytyp`` library is intended to be extensible; the set of polymorphic
ABCs can be extended by users.  This is achieved in the normal Python way,
using a class–based approach with informal protocols based around methods.
For example, the ``normalize()`` function, which converts informal
specifications like ``[int]`` to ABC–based equivalents (``Seq(int)``),
delegates to ``_normalize()`` methods on the ABCs used (and passes itself as
an argument so that recursive conversion of nested values automatically use
any replacement).

Examples
~~~~~~~~

The following are taken from documentation for ``pytyp`` which follows the
general approach described above but is implemented "manually"; the underlying
implementation does not expand to ABCs.

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

This is implemented as a recursive traversal over the type specification and
value, in parallel (a type specification can be quite complex — consider
``[Opt(Map(a=int, b=(int, str)))]``).  If the two are inconsistent at any
point, a ``TypeError`` is raised.

JSON Decoding
.............

Here JSON data, expressed using generic datastructures, is decoded into Python
classes.  The type specification is used to guide the decoding (the argument
to ``make_loads()`` is the type specification we want to construct from the
JSON data)::

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

The implementation uses the same recursive traversal as type checking,
extended to handle the case where a Python class in the specification matches
a JSON dictionary.

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
handling of mutable sequences (settitem v hash).

define everything in terms of new abcs + use register.  make the abcs
parametric.  are abcs transitive(sp?)

types increase granularity of abcs to instances.

