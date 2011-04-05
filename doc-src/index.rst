
Welcome to Pytyp's documentation!
=================================

Pytyp extends the standard JSON and YAML modules to generate arbitrary Python
classes (standard support builds only lists and dicts).  It can also work in
reverse, generating JSON or YAML from existing classes.  This means:

 * Easier integration with systems that communicate using JSON and YAML.

 * Configurations files in a format that is more natural and expressive than
   Python's configparser library.

Although pytyp works with "ordinary" Python classes, you do need to follow
some rules.  These are explained in the documentation for the :mod:`pytyp`
package.  The :mod:`pytyp.json` and :mod:`pytyp.yaml` packages contain
routines for interacting with those two formats.

The mechanism used to implement decoding of "untyped" data streams from JSON
and YAML also supports :ref:`strong_types` (runtime verification of values
against type declarations).

To install from `Pypi <http://pypi.python.org/pypi/pytyp>`_::

  easy_install pytyp

For source see `Google Code <http://code.google.com/p/pytyp/>`_; for support
email `Andrew Cooke <mailto:andrew@acooke.org>`_.

Contents:

.. toctree::
   :maxdepth: 1

   pytyp
   pytyp.json
   pytyp.yaml
   pytyp.spec
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

