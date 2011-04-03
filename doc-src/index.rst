
Welcome to Pytyp's documentation!
=================================

Pytyp populates Python classes with data from JSON and YAML.  It can also work
in reverse, generating JSON or YAML from existing classes.  This means:

 * Easier integration with systems that communicate using JSON and YAML.

 * Configurations files in a format that is more natural and expressive than
   Python's configparser library.

Although pytyp works with "ordinary" Python classes, you do need to follow
some rules.  These are explained in the documentation for the :mod:`pytyp`
package.  The :mod:`pytyp.json` and :mod:`pytyp.yaml` packages contain
routines for interacting with those two formats.

The mechanism used to implement decoding of "untyped" data streams from JSON
and YAML also supports :ref:`strong_types`.

Contents:

.. toctree::
   :maxdepth: 1

   pytyp
   pytyp.json
   pytyp.yaml

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

