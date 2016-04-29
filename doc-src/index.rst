
Welcome to Pytyp's documentation!
=================================

Utilities that help you write declarative code: instead of saying how
something should be done, you describe what the results look like
(:ref:`examples <examples>`).

Pytyp can help you:

Describe Python 3 data in more detail
  :mod:`pytyp.spec.abcs` makes it
  easier to say what you want, and to write libraries that support a
  declarative style.

Map serialised data to Python objects (and back again)
  :mod:`pytyp.s11n` contains modules (:mod:`pytyp.s11n.json` and
  :mod:`pytyp.s11n.yaml`) that transform JSON and YAML data.  This is a good
  example of declarative code - you say what classes you want, and the routine
  works out how to construct them.

Verify function arguments
  :mod:`pytyp.spec.check` provides a decorator to verify that function
  arguments are of the type expected.

Use dynamic dispatch by type
  :mod:`pytyp.spec.dispatch` module lets you split complex functions into
  separate parts, depending on the arguments given.

Use attributes instead of ``[]``, and vice versa
  :mod:`pytyp.spec.record` contains a useful class that is both a dict and an
  object.

.. note::

   The ideas behind this library are described in the paper `Algebraic ABCs
   <http://www.acooke.org/pytyp.pdf>`_.

.. warning::

   This package is unused and largely unmaintained.  Python went in a
   `different direction <https://www.python.org/dev/peps/pep-0484/>`_
   with types.

Installation and Support
------------------------

To install from `PyPI <http://pypi.python.org/pypi/pytyp>`_::

  easy_install pytyp

.. warning::

   This project is Python 3 **only**.

For source see `github <https://github.com/andrewcooke/pytyp>`_; for support
raise an issue there or email `Andrew Cooke <mailto:andrew@acooke.org>`_.

Contents
--------

.. toctree::
   :maxdepth: 1

   pytyp.spec.abcs
   pytyp.s11n
   pytyp.spec.check
   pytyp.spec.dispatch
   licence

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _examples:

Examples
--------

Testing type specifications (:mod:`pytyp.spec.abcs`)::

    >>> isinstance([1,2,None,3], Seq(Opt(int)))
    True
    >>> isinstance([1,2,None,3.0], Seq(Opt(int)))
    False

Creating Python classes from JSON data:



Verifying function arguments (:mod:`pytyp.spec.check`)::

    >>> def myfunction(a:int, b:str) -> int:
    ...     return len(a * b)
    >>> myfunction(2, 'foo')
    6
    >>> myfunction('oops', 'banana')
    Traceback (most recent call last):
      ...
    TypeError: Type str inconsistent with 'oops'.
