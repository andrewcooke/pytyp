
Welcome to Pytyp's documentation!
=================================

Pytyp offers:

 * Easier integration with systems that communicate using :mod:`JSON
   <pytyp.s11n.json>` and :mod:`YAML <pytyp.s11n.yaml>`.

 * Configurations files in a format that is more natural and expressive than
   Python's configparser library.

 * Experimental support for :ref:`strong_types` (runtime verification of
   values against type declarations, typed attributes, and dispatch by type).

To install from `Pypi <http://pypi.python.org/pypi/pytyp>`_::

  easy_install pytyp

For source see `Google Code <http://code.google.com/p/pytyp/>`_; for support
email `Andrew Cooke <mailto:andrew@acooke.org>`_.

Contents:

.. toctree::
   :maxdepth: 1

   pytyp
   pytyp.s11n.json
   pytyp.s11n.yaml
   pytyp.spec.base
   pytyp.spec.check
   pytyp.spec.future
   licence

.. note::

   This project is Python 3 **only**.  You may be able to convert the code to
   write classes to JSON/YAML to Python 2, but the reading code requires
   type annotations, which are not available in earlier versions.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

