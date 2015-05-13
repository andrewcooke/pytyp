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
from pprint import pprint

from pytyp.s11n.base import decode, Encoder


def dump(obj, fp, **kargs):
    '''
    Serialize ``obj`` as a JSON formatted stream to ``fp`` (a
    ``.write()``-supporting file-like object).

    This is intended as a direct substitute for the ``dump()`` function in
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
    :return: None (output written to `fp`)
    '''
    return dump_(obj, fp, cls=JSONEncoder, **kargs)


def dumps(obj, **kargs):
    '''
    Serialize ``obj`` to a JSON formatted string.

    This is intended as a direct substitute for the ``dumps()`` function in
    Python's json package.  It supports the same options, except for `cls`
    (which is used internally to provide Pytyp's own encoding).

    Unlike the standard Python library, this will also encode Python classes
    as long as they follow the conventions described in :ref:`encoding` (in
    short that it has an attribute or property to provide a value for each
    constructor parameter).

    :param obj: The Python object (or collection) to encode.
    :param kargs: Additional parameters are passed directly to the 
                  corresponding routine in Python's json package.
    :return: A string containing the JSON encoded ``obj``.

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
      
    Lists, tuples and dicts of objects are also handled correctly:
    
      >>> dumps((Example('tuple'), {'a': Example('dict'), 'b': [Example('list')]}),
      ...       sort_keys=True)
      '[{"foo": "tuple"}, {"a": {"foo": "dict"}, "b": [{"foo": "list"}]}]'
      
    and this can be read back to Python classes, if the correct type specification 
    is given to `make_loads()`: 
      
      >>> loads = make_loads((Example, {'a': Example, 'b': [Example]}))
      >>> # use pprints to get consistent dict order
      >>> pprint(loads('[{"foo": "tuple"}, {"a": {"foo": "dict"}, "b": [{"foo": "list"}]}]'))
      (<Example(tuple)>, {'a': <Example(dict)>, 'b': [<Example(list)>]})
      
    Even nested classes can be written and read back correctly - see the example for 
    `make_loads()` below.
    '''
    return dumps_(obj, cls=JSONEncoder, **kargs)


class JSONEncoder(JSONEncoder_):
    
    default = Encoder(recurse=False)



def make_load(spec):
    '''
    Create a replacement for the ``load()`` function in Python's json package
    that will deserialize a ``.read()``-supporting file-like object containing a
    JSON document to a Python object.

    :param spec: The type specification for the root object.  Nested objects
                 are defined by type annotations.  See :ref:`decoding` for
                 full details.
    :return: A replacement for ``load()`` in the Python json package, which will
             read from a file are return the data structured as ``spec``.
    '''
    cls = make_JSONDecoder(spec)
    def load(fp, **kargs):
        return load_(fp, cls=cls, **kargs)
    return load


def make_loads(spec):
    '''
    Create a replacement for the ``loads()`` function in Python's json package
    that will deserialize a string containing a JSON document to a Python
    object.

    :param spec: The type specification for the root object.  Nested objects
                 are defined by type annotations.  See :ref:`decoding` for
                 full details.
    :return: A replacement for ``loads()`` in the Python json package, which will
             read from a string are return the data structured as ``spec``.

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
      ...         return '<Container({0})>'.format(','.join(map(repr, self.examples)))
      >>> loads = make_loads(Container)
      >>> loads('[{"foo":"abc"}, {"foo":"xyz"}]')
      <Container(<Example(abc)>,<Example(xyz)>)>
      
    (note that here, because ``Container`` uses ``*args``, it is represented as
    a list, not a dict).
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
    :return: A replacement for the ``JSONDecoder`` class in the Python json 
             package, which returns data structured as ``spec``.
    '''

    class JSONDecoder(JSONDecoder_):
        
        def raw_decode(self, *args, **kargs):
            (decoded, index) = \
                super(JSONDecoder, self).raw_decode(*args, **kargs)
            return (decode(decoded, spec), index)

    return JSONDecoder


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())

