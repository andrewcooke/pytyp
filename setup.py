from setuptools import setup

setup(name='pytyp',
      version='2.2.4',
      description='Pythonic type metadata; declarative JSON and YAML transcoding.',
      long_description='''
Pytyp uses ABCs and function annotations in a consistent, pythonic way that
supports declarative APIs - instead of saying how to do something, you have
the ability to say what you want.

It includes:

* A basic set of type specifications for describing collections of data,
  closely integrated into the language::

    >>> isinstance([1,2,None,4], Seq(Opt(int)))
    True

* A decorator that type-checks functions::

    >>> def str_only(x:str): return 'foo'
    >>> str_only(42)
    Exception raised:
      ...
    TypeError: Type str inconsistent with 42.

* A decorator that allows dynamic dispatch by type.  You can combine multiple
  methods under one name, and then select which method is called by the type
  of an argument (normal OO programming uses the type of ``self`` to select
  the method; this is more like Lisp's multimethods).

* Routines for converting between Python classes and JSON or YAML.  Instead of
  having to work with ``dict`` and ``list`` you can read JSON directly into
  Python classes.  This is included as an example of the declarative API
  possible - you describe the form of the output using type specifications.

The ideas behind the library are described in more detail in `Algebraic ABCs
<http://www.acooke.org/pytyp.pdf>`_.

Note that you must also install `PyYAML
<https://pypi.python.org/pypi/PyYAML>`_ if you want to encode/decode YAML.

Warning: This package is unused and largely unmaintained.  Python went
in a `different direction<https://www.python.org/dev/peps/pep-0484/>`_
with types.  
''',
      author='Andrew Cooke',
      author_email='andrew@acooke.org',
      url='http://www.acooke.org/pytyp/',
      packages=['pytyp', 'pytyp.spec', 'pytyp.s11n'],
      package_dir = {'':'src'},
      keywords = "parser",
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.0',
                   'Programming Language :: Python :: 3.1',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Topic :: Software Development',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Utilities'
                   ]
     )
