
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


Expanding Python's Types
========================

:Author: Andrew Cooke (andrew@acooke.org)
:Version: 0.2 of 14-04-2011

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
``pytyp``.  Originally intended to improve JSON inter-operability, it grew
into a more general toolkit that explored the use of types in Python.  The
approach was *pythonic* --- an optional, runtime system, embedded within the
language, implemented in a library, and based on duck typing.

Here, I record what I learnt and explore how Python might be extended to
better support this approach.  My aim is to identify a small number of changes
to the base language that would improve the consistency and scope of libraries
that want to exploit types (this need not be for type-checking; the original
use case was to allow JSON to inter-operate with used-defined Python classes).

Roadmap
~~~~~~~

In the first section, `Current Status`_, I sketch the runtime type support
that exists in Python.  This shows how ABCs provide a clear, general model for
duck typing.

`Thought Experiments`_ extrapolates from that to explore possible future
developments.  The first few sub-sections are speculative (with some concrete
`Examples`_); the issues raised are then revised and clarified in `Review`_.

Current Status
--------------

Python does not have a statically verified type system, but the language does
have a notion of types.

Classes and Attributes
~~~~~~~~~~~~~~~~~~~~~~

The principal abstraction for structuring source code is ``class``.  This
specifies a set of attributes (directly and through inheritance) for class
instances (objects).  The class associated with an object is universally
referred to as its *type* and available at runtime via the ``type()``
function.

However, the attributes associated with an object are not fixed --- it is
possible to modify any instance through various mechanisms (including
meta-classes and direct manipulation of the underlying dictionaries) --- and
the language runtime does not use the object's type to guide execution [#]_.
Instead, each operation succeeds or fails depending on whether any necessary
*attribute* is present on the instance in question.

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

Despite the approach outlined above some operations still appear specific to
certain types.  For example, the ``float()`` function only works for numerical
types (or strings that can be interpreted as numerical values).  But such
examples can generally be explained in terms of attribute access via "special"
methods (in the case of ``float()`` the method ``__float__()`` on the
function's argument).

I do not know if *every* operation can be explained in terms of attributes,
but my strong impression is that this is the intention: Python is designed to
describe all "type-related" runtime behaviour in terms of attribute access.
In this way it implements (and defines) duck typing.

Recent Extensions
~~~~~~~~~~~~~~~~~

Work related to Python 3 extended the language in two interesting ways.

First, it addressed the conflict described above, which still exists in
theory, even if it is rarely important in practice: on the one hand,
programmers behave as though Python's runtime behaviour can be reliably
explained in terms of types; on the other, the runtime functions in terms of
available attributes.  Abstract Base Classes (ABCs) resolve this contradiction
by identifying collections of attributes, providing a class--like abstraction
that is better suited to duck typing

Second, Python 3 supports (but does enforce) type annotations.  These are
metadata associated with functions.  For example, the following is valid::

  def func(a: int, b:str) -> list:
      return [a, b]

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
associated with types) to be specified on functions.

But there are still many open questions:

* How can we best use the tools we have?  What should type-related metadata
  "mean"?  Are there more compact ways of expressing types in common cases?

* How do types in Python connect with other uses?  How do they match common
  abstractions other languages?  Or in type theory?

* How can types in Python help programmers?  Is static type verification
  possible and useful?  Can types help write more declarative code?

* What is missing from Python (and would be useful to have)?  What language
  changes would help future work?
 
Thought Experiments
-------------------

Typed Collections
~~~~~~~~~~~~~~~~~

To motivate our exploration of how Python might extend support for types
consider the following questions.  How do we define the type of a list of
values?  Or a dictionary?  What if the contents are drawn from an inhomogenous
set of types?

Answering these questions with tools from the previous section would start
with the appropriate container ABC.  This defines the attributes used to
access the data (ie that we have suitable methods to treat the container as a
list, or a dictionary --- more correctly, as a ``Sequence`` or ``Mapping``,
which are ABCs defined in the ``collections`` package).  To define the
contents we must also use type annotations::

  class IntSequence(Sequence):
      def __next__() -> int:
          return super(IntSequence, self).__next__()
      ...

This has some problems [#]_, but is, I hope, a fair extrapolation of Python's
current approach.  One problem is easy to fix: we can define a simpler syntax:
``[int]`` or, more formally, ``Seq(int)`` [#]_.

.. [#] It is verbose, particularly when all methods are defined; type
   annotations don't exist for generators
   http://mail.python.org/pipermail/python-3000/2006-May/002103.html; it's
   unclear how to backfit types to an existing API; type annotations are not
   "implemented"; as is normal with current type systems it supports only
   homogenous sequences)
   
.. [#] The ``normalize()`` function in ``pytyp`` will convert the first
   expression to the second, but there is little reason to do so unless
   ``pytyp`` is extended to include literal values (the distinction between
   values and types becomes important --- we might be referring to a value
   that is a list containing a single value, which happens to be ``int``).

This "natural" syntax can be extended to inhomogenous collections:
dictionaries look like ``{'a':int, 'b':str}``; tuples look like ``(int,
str)``.  But these representations appear tied to specific classes, rather
than the ``Mapping`` ABC.  A better syntax would be ``Map(a=int, b=str)`` or
``Map(int, str)`` (where integer indices are implicit).
   
The step from sequences to maps is more significant than a simple change of
syntax.  When we try to translate ``Map()`` back into ABCs we find that we
need dependent types (the type of the return value from ``__getitem__(key)``
depends on the argument).  This is a consequence of Python using a parametric
approach to records.

A Little Formality
~~~~~~~~~~~~~~~~~~

The previous section introduced a simple shorthand for ABCs with type
annotations.  We will now explore how these "type specifications" fit within
the three core concepts of type theory: product types; parametric
polymorphism; and sum types.

Product Types
.............

The handling of maps above (particularly when using the ``Map(a=int, b=str)``
syntax) is very close to the concept of product types: a container with a
fixed number of values (referenced by label or index), each with a distinct
type.

One small difference between this and product types in other languages is the
structural approach (here there is no name associated with the type).  But
since we are expressing the system in Python this is trivial to correct::

  IntStrRecord = Map(a=int, b=str)

However, ``Map()`` only addresses dicts and tuples.  What about general
classes?  With a significant simplifying assumption --- that the constructor
arguments are present as instance attributes --- we can defined a
"class--like" product type in Python::

  class MyProduct:
      def __init__(self, a:int, b:str):
          self.a = a
          self.b = b

The class--like approach has one significant advantage over ``Map()``: it does
not require dependent types when reduced to ABCs.  This is because each
attribute would be described separately, and so could have its own type.  It
also has a disadvantage: in the reduction to ABCs type annotations in the
constructor [#]_ are related to type annotations for the properties.

.. [#] The alert reader may ask what a constructor is doing in an ABC.  This
   is discussed in the `Review`_ below.

Polymorphism
............

Parametric polymorphism is surprisingly easy.  Again, because we are working
within the language, we can use Python itself::

  def polymorphic_list(param):
      return [param]

or, making the expansion to ABCs in the previous section explicit::

  def Seq(param):
      class TypedSequence(Sequence):
	  def __next__() -> param:
	      return super(TypedSequence, self).__next__()
      ...
      return TypedSequence

If we assume that the type system is inclusive (that subclasses can substitute
for classes) then unbounded polymorphism can be specified as ``Seq(object)``
[#]_.

.. [#] In ``pytyp`` this has the shorthand ``...`` (ellipsis, a singleton
   intended for use in array access, but available generally in Python 3's
   grammar).  For example, ``[...]`` denotes a list of any type.

Sum Types
.........

Python does not have a natural encoding of sum types (alternatives).  We can
invent a notation (with optional labels) --- ``Alt(a=int, b=str)`` --- but
there is no way to reduce this to ABCs.

Despite this, Python does have a common idiom for the most popular sum type,
"Maybe": missing values are represented by ``None``.  We could express this
for integers as ``Maybe(none=None, value=int)`` [#]_.

.. [#] ``pytyp`` has the abbreviation ``Opt()`` for this.

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
value, in parallel (a type specification can be quite complex --- consider
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

A Tree Functor
..............

Finally, a more extreme example that creates a set of classes, parameterised
over a type, to implement a type--checked binary tree.  Please remember that
``pytyp`` is implemented using a *library* and so is purely optional --- the
idea here is to push the limits of what is possible.

I will break the code into chunks with commentary [#]_.  First, we start by
defining a functor (a function that will create a set of classes given a
particular type).  In this case the classes work together to implement a
binary tree.

.. [#] The trailing ``#`` marks force rst2latex to use a consistent indent 
   across blocks.

::

  def tree_functor(leaf_type):

      tree_type = Delayed()

We refer to the type specification for the tree nodes within the code, so must
define it first.  However, we cannot complete the defintion until later, when
we have defined the apropriate classes, so we use ``Delayed()`` as a mutable
placeholder.
::

      class TreeProperty(TypedProperty):

	  def __init__(self, value):
	      super(TreeProperty, self).__init__(value, tree_type)

	  @staticmethod
	  def size(value, spec):
	      return spec.on(value,
			     none=lambda _: 0,
			     leaf=lambda l: 1,
			     node=lambda n: len(n))

	  @staticmethod
	  def set_add(value, spec, leaf:leaf_type):
	      return spec.on(value,
			     none=lambda _: leaf,
			     leaf=lambda l: Node(l).add(leaf),
			     node=lambda n: n.add(leaf))
  #

Adding a ``TypedProperty`` to a subclass of ``Typed`` does two things.  First,
it provides an instance attribute ``.name`` (via Python's property mechanism)
that gives type--checked access to the value.  Second, it populates
``.p.name`` on the class with any additional methods, arranged to so that the
first two arguments are automatically set with the value and type
specification.  This allows us to associate actions with typed values.  The
actions defined above both use dispatch by type --- the code that will be
executed depends on the type of the property's value.  Finally, note that
methods prefixed by ``set_`` mutate the property value with the return value.
::

      class Node(Typed):

	  value = TypedProperty(leaf_type)
	  left = TreeProperty(None)
	  right = TreeProperty(None)

	  @checked
	  def __init__(self, value:leaf_type):
	      super(Node, self).__init__()
	      self.value = value

	  @checked
	  def add(self, value:leaf_type):
	      if value < self.value:
		  self.p.left.set_add(value)
	      else:
		  self.p.right.set_add(value)
	      return self

	  def __len__(self):
	      return 1 + self.p.left.size() + self.p.right.size()
  #

``Node`` is a standard binary tree node.  Actions are implemented through the
typed property methods described earlier.
::

      class Tree(Typed):

	  root = TreeProperty(None)

	  def add(self, value:leaf_type):
	      self.p.root.set_add(value)

	  def __len__(self):
	      return self.p.root.size()
  #

``Tree`` contains a tree root.  Very little code is duplicated from ``Node``
because most of the "heavy lifting" is done in the typed property.
::

      tree_type += Alt(none=None, 
                       leaf=leaf_type, 
                       node=Node)
      return Tree
  #

At this point we can complete the type defintion: the ``tree_type`` properties
can be empty, contain a single value, or be a node with children.
::

  Tree = tree_functor(int)
  t1 = Tree()
  t1.add(1)

This creates an ``int`` tree and adds a first value.

Review
~~~~~~

Python's existing features, ABCs and type annotations, used within the Python
language (ie. at runtime) appear capable of expressing both product types and
parametric polymorphism.  The work required by a programmer to exploit these
measures directly would be significant, but might be reduced by a library
providing a higher--level interface.

However, many problems remain.  I will now discuss these.

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

Incomplete Type Annotations
...........................

Generators do not support type annotations.  This makes 

Generators.  References to "self" or the current class.

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

Conclusions
-----------

[Check what ABCs actually do]

Embedding --- Solves many problems, but makes optimisation hard.


