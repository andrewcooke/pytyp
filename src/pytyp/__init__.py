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

from inspect import getfullargspec, getcallargs
from collections import Callable, Iterable
from pytyp.spec import dispatch


DEFAULT_RAW = (str,int,float,bool)
'''
Types that are not explicitly encoded, but instead passed through as raw
values.
'''


def encode(obj, raw=DEFAULT_RAW, recurse=True, check_circular=True, 
           strict=True):
    '''
    Encode a Python class as a dictionary.  This function can also encode
    lists, tuples and dictionaries containing classes, and nested classes.

    :param obj: The object to be encoded.
    :param raw: Types that are not explicitly encoded, but passed through
                as raw values (by default, `DEFAULT_RAW`).
    :param recurse: Recursively encode values?  `encode` is designed to be
                    used with other encodes; sometimes these expect only
                    a single value to be encoded (`recurse=False`).
    :param check_circular: If `True`, an error is rased for circular
                           references (if disabled the encoding may loop
                           indefinitely).
    :param strict: If `True`, fail when constructor parameters with default
                   values have no corresponding attribute.

    To encode data, pytyp looks at the constructor arguments.  For each
    argument it assumes that the class has an attribute or property that
    provides a value.

    So, for example, this class can be encoded::

      >>> class EncExample():
      ...     def __init__(self, a, b=None):
      ...         self.a = a
      ...         self.b = b
      ...
      >>> encode(EncExample(1, 2))
      {'a': 1, 'b': 2}

    but this class cannot::

      >>> class BadEncExample():
      ...     def __init__(self, q):
      ...         self.z = q
      ...
      >>> encode(BadEncExample(1))
      Traceback (most recent call last):
        ...
      AttributeError: 'BadEncExample' object has no attribute 'q'

    If you do not want your objects to be mutable you can expose the same
    information through read-only properties::

      >>> class ReadOnly():
      ...     def __init__(self, value):
      ...         self._value = value
      ...     @property
      ...     def value(self):
      ...         return self._value
      ...
      >>> encode(ReadOnly(1))
      {'value': 1}
    '''
    
    if type(obj) in raw:
        return obj
    
    if check_circular is True:
        check_circular = set([id(obj)])
    elif check_circular:
        if id(obj) in check_circular:
            raise ValueError('Circular reference at {0}'.format(obj))
        else:
            check_circular.add(id(obj))
            
    encode_ = lambda o: encode(o, raw=raw, recurse=recurse, 
                               check_circular=check_circular, strict=strict)
    
    if isinstance(obj, list):
        return list(map(encode_, obj))
    
    if isinstance(obj, tuple):
        return tuple(map(encode_, obj))
    
    if isinstance(obj, dict):
        return dict((name, encode_(obj[name])) for name in obj)
    
    spec = getfullargspec(obj.__class__.__init__)
        
    def check(name, eq, type_):
        value = getattr(obj, name)
        if isinstance(value, type_) != eq:
            raise TypeError('{0} for {1} is {2}of type {3}'.format(
                    name, type(obj), '' if eq else 'not ', type_))
        if recurse:
            value = encode_(value)
        return (name, value)
    
    def unpack():
        for name in spec.args[1:]: # skip self
            # reject Callable to catch the common case of methods
            yield check(name, False, Callable)
        if spec.varargs:
            yield check(spec.varargs, True, Iterable)
        try:
            if spec.varkw:
                yield check(spec.varkw, True, dict)
        except AttributeError:
            if strict: raise
        try:
            for name in spec.kwonlyargs:
                yield check(name, False, Callable)
        except AttributeError:
            if strict: raise
            
    return dict(unpack())


def decode(spec, value):
    '''
    Decode a dictionary of data as a Python class.  This function can also 
    decode lists, tuples and dictionaries of values, and nested values.

    :param spec: The class (more generally, the type specification - see
                 below) to create.
    :param value: The data to decode.

    To decode data, pytyp looks at the type specification and constructs
    the class by calling the constructor.  The specification can contain
    lists, tuples and dictionaries, but must have the same form as the input.

    For example, here `decode()` is called with a type specification for a
    list of `DecExample()` instances::
    
      >>> class DecExample():
      ...     def __init__(self, a):
      ...         self.a = a
      ...     def __repr__(self):
      ...         return '<DecExample({0})>'.format(self.a)
      ...
      >>> decode([DecExample], [{'a': 1}, {'a': 2}])
      [<DecExample(1)>, <DecExample(2)>]

    To handle nested types the constructor of the container class must have
    a type declaration (another type specification)::

      >>> class Container():
      ...     def __init__(self, ex:DecExample):
      ...         self.ex = ex
      ...     def __repr__(self):
      ...         return '<Container({0})>'.format(self.ex)
      ...
      >>> decode(Container, {'ex': {'a': 1}})
      <Container(<DecExample(1)>)>

    Note the type declaration in the constructor above.  Without that
    declaration pytyp will incorrectly interpret the data::

      >>> class BadContainer():
      ...     def __init__(self, ex):
      ...         self.ex = ex
      ...     def __repr__(self):
      ...         return '<BadContainer({0})>'.format(self.ex)
      ...
      >>> decode(BadContainer, {'ex': {'a': 1}})
      <BadContainer({'a': 1})>

    In type specifications, lists must be of a single type, but tuples and
    dicts have a specific type for each member::
    
      >>> decode((Container, DecExample), ({'ex': {'a': 1}}, {'a': 2}))
      (<Container(<DecExample(1)>)>, <DecExample(2)>)

    A value of None can be matched by an optional type::

      >>> decode((Opt(Container), DecExample), (None, {'a': 2}))
      (None, <DecExample(2)>)
    '''
    return dispatch(spec, value,
        on_single=lambda spec, value: value,
        on_sequence=lambda spec, value: [decode(spec, v) for v in value],
        on_record=lambda nsv: ((n, decode(s, v)) for (n, s, v) in nsv),
        coerce_dict_to_class=lambda cls, args, kargs: cls(*args, **kargs))


if __name__ == "__main__":
    import doctest
    doctest.testmod()

