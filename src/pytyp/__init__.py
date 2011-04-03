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
from collections import Callable, Iterable, Mapping, Sequence, Iterator
from functools import reduce
from itertools import count
from operator import __and__


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
    lists and tuples, but must have the same form as the input.

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
        on_list=lambda spec, value: [decode(spec, v) for v in value],
        on_record=lambda nsv: [(n, decode(s, v)) for (n, s, v) in nsv],
        coerce_dict_to_class=lambda cls, args, kargs: cls(*args, **kargs))


def validate(spec, value):
    '''
    Check a value against a type specification.  Raises an error on failure.

    This uses the same approach as described above: simple types and
    collections work as expected; `None` matches any type; `Opt()` indicates
    an optional value and `Choice()` a choice:

      >>> validate(str, 'abc')
      >>> validate(None, 'abc')
      >>> validate(str, None)
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/None
      >>> validate(Opt(str), None)
      >>> validate(str, 1)
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/1
      >>> validate(Choice(str, int), 1)
      >>> validate(Choice(str, int), 'abc')

    Dictionaries are typed by name; values are required and additional values
    accepted:

      >>> validate({'a': int, 'b': str}, {'a': 1, 'b': 'two'})
      >>> validate({'a': int, 'b': str}, {'a': 1, 'b': 'two', 'c':3.4})
      >>> validate({'a': int, 'b': str}, {'a': 1})
      Traceback (most recent call last):
        ...
      TypeError: Missing value for b
      >>> validate({'a': int, 'b': Opt(str)}, {'a': 1})
      >>> validate({'a': int, 'b': Choice(str, int)}, {'a': 1, 'b': 'two'})
      >>> validate({'a': int, 'b': Choice(str, int)}, {'a': 1, 'b': 2})

    Lists match squences of the same type:

      >>> validate([int], [])
      >>> validate([int], [1])
      >>> validate([int], [1, 2])
      >>> validate([int], (1, 2))
      >>> validate([int], [1, 'two'])
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/two
      >>> validate([Choice(int, str)], [1, 'two'])

    Tuples allow different types, but lengths must match:

      >>> validate((int,), [])
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [])
      >>> validate((int,), [1])
      >>> validate((int, str), [1, 'two'])
      >>> validate((int, str), (1, 'two'))
      >>> validate((int,), [1, 'two'])
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [1, 'two'])
      >>> validate((int, str), (1, 2))
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/2
      >>> validate((int, Choice(int, str)), (1, 2))

    Named tuples match both dictionaries and sequences:

      >>> from collections import namedtuple
      >>> NT = namedtuple('NT', 'a, b')
      >>> validate(NT, NT('class', 'only'))
      >>> validate(NT(int, str), NT(1, b='two'))
      >>> validate(NT(int, str), NT(b=1, a='two'))
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/two
      >>> validate(NT(int, str), [1, 'two'])
      >>> validate(NT(int, str), {'a': 1, 'b': 'two'})
      >>> validate(NT(int, Opt(str)), {'a': 1, 'b': None})
      >>> validate(NT(None, str), {'a': 'anything', 'b': 'two'})
      >>> validate(NT(Choice(str, int), Choice(str, int)), {'a': 'one', 'b': 2})

    but the number of entries must match exactly:

      >>> validate(NT(int, str), {'a': 1, 'b': 'two', c: 'extra'})
      Traceback (most recent call last):
        ...
      NameError: name 'c' is not defined
      >>> validate(NT(int, str), {'b': 'two'})
      Traceback (most recent call last):
        ...
      KeyError: 'a'
      >>> validate(NT(int, Opt(str)), {'a': 1})
      Traceback (most recent call last):
        ...
      KeyError: 'b'
    '''
    dispatch(spec, value,
        on_single=lambda spec, value: None,
        on_list=lambda spec, value: [validate(spec, v) for v in value],
        on_record=lambda nsv: [(n, validate(s, v)) for (n, s, v) in nsv],
        coerce_dict_to_class=None)


class Opt():
    '''
    Construct an optional type specification.  This allows values of None
    to be matched.

      >>> validate(Opt(int), 1)
      >>> validate(Opt(int), None)
      >>> validate(Opt(int), 'one')
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/one
    '''
    
    def __init__(self, spec):
        self.spec = spec
        
        
class Choice():
    '''
    Construct a sum (union) type specification.

      >>> validate(Choice(int, str), 1)
      >>> validate(Choice(int, str), 'two')
      >>> validate(Choice(int, str), 3.0)
      Traceback (most recent call last):
        ...
      TypeError: No choice in (<class 'int'>, <class 'str'>) for 3.0
    '''
    
    def __init__(self, *spec):
        self.spec = spec
        
        
def dispatch(spec, value,
             on_single, # f(spec, value) -> value
             on_list, # f(spec, value) -> list
             on_record, # f(iter(name, spec, value)) -> iter(name, value)
             coerce_dict_to_class=None # f(cls, *args, **kargs) -> cls
             ):
    '''
    The core of the type system, this matches a value against a type
    specification and calls the appropriate handler function.
    
    `Opt()` and `Choice()` are handled internally (by recursion as needed).

    :param spec: Type specification.
    :param value: Value whose type should match the specification.
    :param on_single: Called when a simple value is found.
    :param on_list: Called when a list of values are found.
    :param on_record: Called when an ordered set of values are found.
    :param coerce_dict_to_class: Called, if defined, when a `dict` matches
                                 a class type specification (used for 
                                 unpacking JSON and YAML data).
    '''
    
    if spec is None:
        return on_single(spec, value)
    
    if isinstance(spec, Opt):
        if value is None:
            return on_single(spec, value)
        else:
            return dispatch(spec.spec, value,
                            on_single, on_list, on_record, coerce_dict_to_class)

    if isinstance(spec, Choice):
        for s in spec.spec:
            try:
                return dispatch(s, value,
                                on_single, on_list, on_record, coerce_dict_to_class)
            except:
                pass
        raise TypeError('No choice in {0} for {1}'.format(spec.spec, value))

    if isinstance(spec, list):
        if len(spec) != 1:
            raise TypeError('Lists must be of a single type '
                            '(not {0})'.format(spec))
        return on_list(spec[0], value)
    
    if type(spec) is tuple:
        if isinstance(value, Iterator):
            value = list(value)
        if len(spec) != len(value):
            raise TypeError('Tuples must match input data in length '
                            '({0} does not match {1})'.format(spec, value))
        return tuple(v for (_, v) in on_record(zip(count(), spec, value)))
    
    # namedtuples
    if isinstance(spec, tuple):
        # convert dict to sequence
        if isinstance(value, Mapping):
            value = [value[name] for name in spec._fields]
        if len(spec) != len(value):
            raise TypeError('Tuples must match input data in length '
                            '({0} does not match {1})'.format(spec, value))
        return type(spec)(*(v 
                    for (_, v) in on_record(zip(count(), spec, value))))
    
    if isinstance(spec, dict):
        names = set(spec.keys())
        names.update(value.keys())
        for name in names:
            if name not in value and not isinstance(spec[name], Opt):
                raise TypeError('Missing value for {0}'.format(name))
        return dict(on_record((name, spec.get(name, None), value[name]) 
                              for name in names if name in value))

    if not isinstance(spec, type):
        raise TypeError('Expected type (not {0})'.format(spec))
    
    if isinstance(value, spec):
        return on_single(spec, value)
    
    if not coerce_dict_to_class:
        raise TypeError('Unexpected type or value: {0}/{1}'.format(spec, value))

    if not isinstance(value, dict):
        raise TypeError('Need dict to unpack {0} (not {1})'.format(spec, value))
    
    argspec = getfullargspec(spec.__init__)
    # ignore missing values; they will be caught by constructor application
    unpacked = dict(on_record((name, 
                               argspec.annotations.get(name, None), 
                               value[name]) 
                              for name in value))
    args = unpacked.pop(argspec.varargs, ())
    kargs = unpacked.pop(argspec.varkw, {})
    kargs.update(unpacked)
    return coerce_dict_to_class(spec, args, kargs)


def checked(func):
    '''
    A decorator that adds type checking to a function or method.

      >>> @checked
      ... def str_len(s:str) -> int:
      ...     return len(s)
      >>> str_len('abc')
      3
      >>> str_len([1,2,3])
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/[1, 2, 3]
      >>> @checked
      ... def bad_len(s:str) -> int:
      ...     return 'wrong'
      >>> bad_len('abc')
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/wrong
    '''
    def wrapper(*args, **kargs):
        callargs = getcallargs(func, *args, **kargs)
        annotations = getfullargspec(func).annotations
        rspec = annotations.pop('return', None)
        for name in annotations:
            spec = annotations[name]
            value = callargs.get(name, None)
            validate(spec, value)
        result = func(*args, **kargs)
        validate(rspec, result)
        return result
    return wrapper


if __name__ == "__main__":
    import doctest
    doctest.testmod()

