
Welcome to Pytyp's documentation!
=================================

.. warning::

   This project is Python 3 **only**.

Pytyp is a small collection of utilities that help you write declarative code:
instead of saying how something should be done, you describe what the results
look like.

* The :mod:`pytyp.spec.abcs` module gives you tools to describe Python
  3 data in more detail.  This makes it easier to say what you want, and to
  write libraries that support a declarative style.

* The :mod:`<pytyp.s11n>` package contains modules (:mod:`JSON
  <pytyp.s11n.json>` and :mod:`YAML <pytyp.s11n.yaml>`) that map serialised
  data to Python objects (and back again).  This is a good example of
  declarative code - you say what classes you want, and the routine works out
  how to construct them.

* The :mod:`check <pytyp.spec.check>` module provides a decorator to verify
  that function arguments are of the type expected.

* The :mod:`dispatch <pytyp.spec.dispatch>` module supports dynamic dispatch
  by type.  This lets you split complex functions into separate parts,
  depending on the arguments given.

* The :mod:`checkrecord <pytyp.spec.record>` module contains a useful class
  that is both a dict and an object (so you can use attributes instead of 
  ``[]``, and vice versa).

.. warning::

   The library has been almost completely rewritten for the 2.0 release.
   Public APIs have changed.  You may need to fix your code when updating.

To install from `Pypi <http://pypi.python.org/pypi/pytyp>`_::

  easy_install pytyp

For source see `Google Code <http://code.google.com/p/pytyp/>`_; for support
email `Andrew Cooke <mailto:andrew@acooke.org>`_.

Contents:

.. toctree::
   :maxdepth: 1

   pytyp.spec.abcs
   pytyp.s11n
   pytyp.spec.check
   pytyp.spec.dispatch
   licence

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

