
.. automodule:: pytyp.spec.dispatch

.. testsetup::

  from pytyp.spec.dispatch import *

.. _verification:

Dynamic Dispatch by Type
========================

This module provides a decorator that lets you choose which method is called
via :ref:`type specifications <type_specs>`.

.. hint::

  There is a good example of the decorator in use in `the source for Encoder
  <_modules/pytyp/s11n/base.html#Encoder>`_; more details are available in the
  paper `Algebraic ABCs <http://www.acooke.org/pytyp.pdf>`_.

.. autofunction:: overload
.. autoclass:: Overload
