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

from json import JSONDecoder as JSONDecoder_, load as load_, loads as loads_, \
    JSONEncoder as JSONEncoder_, dump as dump_, dumps as dumps_

from pytyp import encode, DEFAULT_RAW, decode


def dump(obj, fp, **kargs):
    '''
    Serialize `obj` as a JSON formatted stream to `fp` (a
    `.write()`-supporting file-like object).

    This is intended as a direct substitute for the `dump()` function in
    Python's json package.  It supports the same options, except for `cls`
    (which is used internally to provide Pytyp's own encoding).

    Unlike the standard Python library, this will also encode Python classes
    as long as they follow the conventions described in :ref:`encoding` (in
    short that it has an attribute or property to provide a value for each
    constructor parameter).

    :param obj: The Python object (or collection) to encode.
    :param fp: The destination for the data.
    :param kargs: Additional parameters are passed directly to the 
                  corresponding routine in Python's json package.
    '''
    return dump_(obj, fp, cls=JSONEncoder, **kargs)


def dumps(obj, **kargs):
    '''
    Serialize obj to a JSON formatted string.

    Again, intended as a direct substitute for the function in Python's json
    package.

    :param obj: The Python object (or collection) to encode.
    :param kargs: Additional parameters are passed directly to the 
                  corresponding routine in Python's json package.

    Here is an example of encoding a Python class, and then reading that back
    from JSON:

      >>> class Example():
      ...     def __init__(self, foo):
      ...         self.foo = foo
      ...     def __repr__(self):
      ...         return '<Example({0})>'.format(self.foo)
      >>> dumps(Example('abc'))
      '{"foo": "abc"}'
      >>> loads = make_loads(Example)
      >>> loads('{"foo": "abc"}')
      <Example(abc)>
    '''
    return dumps_(obj, cls=JSONEncoder, **kargs)


def make_JSONEncoder(raw):

    class JSONEncoder(JSONEncoder_):
        
        def default(self, obj):
            return encode(obj, raw=raw, recurse=False)
        
    return JSONEncoder


JSONEncoder = make_JSONEncoder(DEFAULT_RAW)
'''
A custom encoder for the Python json module.
'''


def make_load(spec):
    '''
    Create a replacement for the `load()` function in Python's json package
    that will deserialize a `.read()`-supporting file-like object containing a
    JSON document to a Python object.

    :param spec: The type specification for the root object.  Nested objects
                 are defined by type annotations.  See :ref:`decoding` for
                 full details.
    '''
    cls = make_JSONDecoder(spec)
    def load(fp, **kargs):
        return load_(fp, cls=cls, **kargs)
    return load


def make_loads(spec):
    '''
    Create a replacement for the `loads()` function in Python's json package
    that will deserialize a string containing a JSON document to a Python
    object.

    :param spec: The type specification for the root object.  Nested objects
                 are defined by type annotations.  See :ref:`decoding` for
                 full details.

    For example:

      >>> class Example():
      ...     def __init__(self, foo):
      ...         self.foo = foo
      ...     def __repr__(self):
      ...         return '<Example({0})>'.format(self.foo)
      >>> class Container():
      ...     def __init__(self, *examples:[Example]):
      ...         self.examples = examples
      ...     def __repr__(self):
      ...         return '<Container({0})>'.\
                      format(','.join(map(repr, self.examples)))
      >>> loads = make_loads(Container)
      >>> loads('{"examples": [{"foo":"abc"}, {"foo":"xyz"}]}')
      <Container(<Example(abc)>,<Example(xyz)>)>
    '''
    cls = make_JSONDecoder(spec)
    def loads(s, **kargs):
        return loads_(s, cls=cls, **kargs)
    return loads


def make_JSONDecoder(spec):
    '''
    Create a custom decoder for the Python json module.

    :param spec: The type specification for the root object.  Nested objects
                 are defined by type annotations.  See :ref:`decoding` for
                 full details.
    '''

    class JSONDecoder(JSONDecoder_):
        
        def decode(self, *args, **kargs):
            return decode(spec, super(JSONDecoder, self).decode(*args, **kargs))
    
        def raw_decode(self, *args, **kargs):
            (decoded, index) = \
                super(JSONDecoder, self).raw_decode(*args, **kargs)
            return (decode(spec, decoded), index)

    return JSONDecoder


if __name__ == "__main__":
    import doctest
    doctest.testmod()

