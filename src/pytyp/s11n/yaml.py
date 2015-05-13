# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and
# limitations under the License.
#
# The Original Code is Pytyp (http://www.acooke.org/pytyp)
# The Initial Developer of the Original Code is Andrew Cooke.
# Portions created by the Initial Developer are Copyright (C) 2011
# Andrew Cooke. All Rights Reserved.
#
# Alternatively, the contents of this file may be used under the terms
# of the LGPL license (the GNU Lesser General Public License,
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions
# of the LGPL License are applicable instead of those above.
#
# If you wish to allow use of your version of this file only under the
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions
# above, a recipient may use your version of this file under either the
# MPL or the LGPL License.

try:
    from yaml import safe_dump, safe_dump_all, safe_load, safe_load_all

    from pytyp.s11n.base import encode, decode
    
    
    def dump(data, stream=None, **kargs):
        '''
        Serialize `data` as a YAML formatted stream (or return a string).

        :param data: The Python object (or collection) to encode.
        :param stream: The destination for the data.
        :param kargs: Additional parameters are passed directly to the 
                      corresponding routine in pyyaml.
        :return: A string containing YAML encoded `data` if `stream` is 
                 `None`; otherwise `None` (output written to `stream`).

        Here is an example of encoding a Python class, and then reading that
        back from YAML:

          >>> class Example():
          ...     def __init__(self, foo):
          ...         self.foo = foo
          ...     def __repr__(self):
          ...         return '<Example({0})>'.format(self.foo)
          >>> dump(Example('abc'))
          '{foo: abc}\\n'
          >>> load = make_load(Example)
          >>> load('{foo: abc}')
          <Example(abc)>
        '''
        return safe_dump(encode(data), stream=stream, **kargs)
    
    
    def dump_all(data, stream=None, **kargs):
        '''
        Serialize a sequence of values as a YAML formatted stream (or return a
        string).

        :param data: A generators of Python values.
        :param stream: The destination for the data.
        :param kargs: Additional parameters are passed directly to the 
                      corresponding routine in pyyaml.
        :return: A string containing YAML encoded `data` if `stream` is 
                 `None`; otherwise `None` (output written to `stream`).

        Here is an example of encoding a series of Python classes, and then
        reading that back from YAML:

          >>> class Example():
          ...     def __init__(self, foo):
          ...         self.foo = foo
          ...     def __repr__(self):
          ...         return '<Example({0})>'.format(self.foo)
          >>> dump_all([Example('abc'), Example('xyz')])
          '{foo: abc}\\n--- {foo: xyz}\\n'
          >>> load_all = make_load_all([Example, Example])
          >>> list(load_all('{foo: abc}\\n--- {foo: xyz}\\n'))
          [<Example(abc)>, <Example(xyz)>]

        .. note::
        
          The `_all()` routines work with YAML's support for multiple
          documents.  Each document is handled separately and the list
          `[Example, Example]` above, as an argument to `make_load_all()`, is
          not a type specification, but an iterable collection of type
          specifications, one per document.
        '''
        return safe_dump_all((encode(d) for d in data), 
                             stream=stream, **kargs)
    
    
    def make_load(spec):
        '''
        Create a replacement for the `load()` function in pyyaml that will
        deserialize a stream containing a YAML document to a Python object.

        :param spec: The type specification for the root object.  Nested
                     objects are defined by type annotations.  See
                     :ref:`decoding` for full details.
        :return: A replacement for `load()` in the PyYAML package which
                 returns data structure as `spec`.

        The documentation for `dump()` above contains an example of use.
        '''
        def load(stream, **kargs):
            return decode(safe_load(stream, **kargs), spec)
        return load
    
    
    def make_load_all(spec):
        '''
        Create a replacement for the `load_all()` function in pyyaml that will
        deserialize a stream containing multiple YAML documents to Python
        objects.

        :param spec: A generator giving type specifications for the root
                     objects.  Nested objects are defined by type annotations.
                     See :ref:`decoding` for full details.
        :return: A replacement for `load_all()` in the PyYAML package which
                 returns data structure as `spec`.

        The documentation for `dump_all()` above contains an example of use.
        '''
        def load_all(stream, **kargs):
            for (s, d) in zip(spec, safe_load_all(stream, **kargs)):
                yield decode(d, s)
        return load_all

except ImportError:

    def _lazy():
        raise ImportError('Please install PyYAML - eg easy_install pyyaml')

    def dump(data, stream=None, **kargs):
        _lazy()

    def dump_all(data, stream=None, **kargs):
        _lazy()

    def make_load(spec):
        _lazy()

    def make_load_all(spec):
        _lazy()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

