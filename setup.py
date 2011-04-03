from setuptools import setup

setup(name='pytyp',
      version='1.0',
      description='JSON and YAML interoperation for Python 3 using type annotations',
      long_description='''
Pytyp populates Python 3 classes with data from JSON and YAML. It can also
work in reverse, generating JSON or YAML from existing classes. This means:

Easier integration with systems that communicate using JSON and YAML.
Configurations files in a format that is more natural and expressive than
Python’s configparser library.  Although pytyp works with “ordinary” Python
classes, you do need to follow some rules. These are explained in the
documentation for the pytyp package. The pytyp.json and pytyp.yaml packages
contain routines for interacting with those two formats.

The mechanism used to implement decoding of “untyped” data streams from JSON
and YAML also supports runtime verification of values against type
declarations for Python 3.
''',
      author='Andrew Cooke',
      author_email='andrew@acooke.org',
      url='http://www.acooke.org/pytyp/',
      packages=['pytyp'],
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
                   'Topic :: Software Development',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Utilities'
                   ]
     )
