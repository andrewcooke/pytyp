
.. automodule:: pytyp.spec.check

.. testsetup::

  from pytyp.spec.check import *

.. _verification:

Verification (pytyp.spec.check)
===============================

This module provides routines to verify :ref:`type specifications
<type_specs>`.

A value is verified in one of four ways:

#. If the value is a subclass of the specification.

#. If the value's class is registered with the specification (using the
   ``register()`` method).

#. If the value is registered with the specification (using the
   ``register_instance()`` method).

#. If the value is a container that can be :ref:`iterated over <iteration>`
   and whose contents can be verified.

The last of these must inspect all values, so can be inefficient.

Checked
-------

.. autofunction:: checked

Verify
------

.. autofunction:: verify
