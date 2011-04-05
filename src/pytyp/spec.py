#LICENCE

from inspect import getfullargspec, getcallargs
from collections import Iterator
from functools import wraps
from itertools import count


def verify(spec, value):
    '''
    Check a value against a type specification.  Raises an error on failure.

    This uses the same approach as described above: simple types and
    collections work as expected; `None` matches any type; `Opt()` indicates
    an optional value and `Choice()` a choice:

      >>> verify(str, 'abc')
      >>> verify(None, 'abc')
      >>> verify(str, None)
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/None
      >>> verify(Opt(str), None)
      >>> verify(str, 1)
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/1
      >>> verify(Choice(str, int), 1)
      >>> verify(Choice(str, int), 'abc')

    Dictionaries are typed by name, values are required unless optional:

      >>> verify({'a': int, 'b': str}, {'a': 1, 'b': 'two'})
      >>> verify({'a': int, 'b': str}, {'a': 1, 'b': 'two', 'c':3.4})
      Traceback (most recent call last):
        ...
      TypeError: Additional field(s): c
      >>> verify({'a': int, 'b': str}, {'a': 1})
      Traceback (most recent call last):
        ...
      TypeError: Missing value for b
      >>> verify({'a': int, Opt('b'): str}, {'a': 1})
      >>> verify({'a': int, 'b': Choice(str, int)}, {'a': 1, 'b': 'two'})
      >>> verify({'a': int, 'b': Choice(str, int)}, {'a': 1, 'b': 2})

    Lists match sequences of the same type:

      >>> verify([int], [])
      >>> verify([int], [1])
      >>> verify([int], [1, 2])
      >>> verify([int], (1, 2))
      >>> verify([int], [1, 'two'])
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/two
      >>> verify([Choice(int, str)], [1, 'two'])

    Tuples allow different types, but lengths must match:

      >>> verify((int,), [])
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [])
      >>> verify((int,), [1])
      >>> verify((int, str), [1, 'two'])
      >>> verify((int, str), (1, 'two'))
      >>> verify((int,), [1, 'two'])
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [1, 'two'])
      >>> verify((int, str), (1, 2))
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'str'>/2
      >>> verify((int, Choice(int, str)), (1, 2))
    '''
    dispatch(spec, value,
        on_single=lambda spec, value: None,
        on_sequence=lambda spec, value: [verify(spec, v) for v in value],
        on_record=lambda nsv: ((n, verify(s, v)) for (n, s, v) in nsv),
        coerce_dict_to_class=None)


class Modifier():
    
    def __init__(self, spec):
        self.spec = spec
        
    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.spec == self.spec
    
    def __hash__(self):
        return hash(self.__class__) ^ hash(self.spec)
    
    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self.spec)
    


class Opt(Modifier):
    '''
    Construct an optional type specification.  This allows values of None
    to be matched.

      >>> verify(Opt(int), 1)
      >>> verify(Opt(int), None)
      >>> verify(Opt(int), 'one')
      Traceback (most recent call last):
        ...
      TypeError: Unexpected type or value: <class 'int'>/one
      >>> repr(Opt(int))
      "Opt(<class 'int'>)"
      >>> str(Opt(int))
      "<class 'int'>?"
    '''
    
    def __str__(self):
        return str(self.spec) + '?'

    @staticmethod
    def strip(opt):
        try:
            return opt.spec
        except AttributeError:
            return opt
        
        
class Choice(Modifier):
    '''
    Construct a sum (union) type specification.

      >>> verify(Choice(int, str), 1)
      >>> verify(Choice(int, str), 'two')
      >>> verify(Choice(int, str), 3.0)
      Traceback (most recent call last):
        ...
      TypeError: No choice in (<class 'int'>, <class 'str'>) for 3.0
      >>> repr(Choice(int, str))
      "Choice((<class 'int'>, <class 'str'>))"
      >>> str(Choice(int, str))
      "(<class 'int'>|<class 'str'>)"
    '''
    
    def __init__(self, *spec):
        super(Choice, self).__init__(spec)
    
    def __str__(self):
        return '({0})'.format('|'.join(map(str, self.spec)))
        
    def __rer__(self):
        return 'Choice({0})'.format(','.join(map(repr, self.spec)))
        
        
def dispatch(spec, value,
             on_single, # f(spec, value) -> value
             on_sequence, # f(spec, value) -> list
             on_record, # f(iter(name, spec, value)) -> iter(name, value)
             coerce_dict_to_class=None # f(cls, *args, **kargs) -> cls
             ):
    '''
    The core of the type system, this matches a value against a type
    specification and calls the appropriate handler function on success.
    
    `Opt()` and `Choice()` are handled internally (by recursion and 
    try/fail, as needed).

    :param spec: Type specification.
    :param value: Value whose type should match the specification.
    :param on_single: Called when a simple value is found.
    :param on_sequence: Called when a sequence of values are found.
    :param on_record: Called when an ordered set of values are found.
    :param coerce_dict_to_class: Called, if defined, when a class type
                                 specification coincides with a `dict`
                                 value (used for unpacking JSON and 
                                 YAML data).
    '''
    
    if spec is None:
        return on_single(spec, value)
    
    if isinstance(spec, Opt):
        if value is None:
            return on_single(spec, value)
        else:
            return dispatch(spec.spec, value,
                            on_single, on_sequence, on_record, coerce_dict_to_class)

    if isinstance(spec, Choice):
        for s in spec.spec:
            try:
                return dispatch(s, value,
                                on_single, on_sequence, on_record, coerce_dict_to_class)
            except:
                pass
        raise TypeError('No choice in {0} for {1}'.format(spec.spec, value))

    if isinstance(spec, list):
        if len(spec) != 1:
            raise TypeError('Lists must be of a single type '
                            '(not {0})'.format(spec))
        return on_sequence(spec[0], value)
    
    if isinstance(spec, tuple):
        if isinstance(value, Iterator):
            value = list(value)
        if len(spec) != len(value):
            raise TypeError('Tuples must match input data in length '
                            '({0} does not match {1})'.format(spec, value))
        return tuple(v for (_, v) in on_record(zip(count(), spec, value)))
    
    def dispatch_dict(spec):
        names = set(value.keys())
        for name in spec:
            if name not in value and not isinstance(name, Opt):
                raise TypeError('Missing value for {0}'.format(name))
            names.discard(Opt.strip(name))
        if names:
            raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
        return dict(on_record((Opt.strip(name), spec[name], value[Opt.strip(name)]) 
                              for name in spec if Opt.strip(name) in value))
    
    if isinstance(spec, dict):
        return dispatch_dict(spec)

    if not isinstance(spec, type):
        raise TypeError('Expected type (not {0})'.format(spec))
    
    if isinstance(value, spec):
        return on_single(spec, value)
    
    if not coerce_dict_to_class or not isinstance(value, dict):
        raise TypeError('Unexpected type or value: {0}/{1}'.format(spec, value))
    
    # if we're here, we have a class spec and a dict value
    (varargs, varkw, dict_spec) = class_to_dict_spec(spec)
    new_value = dispatch_dict(dict_spec)
    args = new_value.pop(varargs, ())
    kargs = new_value.pop(varkw, {})
    kargs.update(new_value)    
    return coerce_dict_to_class(spec, args, kargs)


def class_to_dict_spec(cls):
    '''
    Create a type specification for a dict, given a class.  This reads any
    type annotation, adds positional args as required, and adds keyword args
    (with defaults) as optional.
    
    :param cls: The class to encode
    :return (varargs, varkw, spec): Where `varargs` is the name of the `*args`
                                    parameter (or `None`); `varkw` is the name
                                    of the `**kargs` parameter (or `None`) and
                                    `spec` is the type specification.
    
    >>> class Example():
    ...     def __init__(self, pos, ann:str, ann_deflt:int=42, *varargs, kwonly, kwonly_deflt='value', **varkw):
    ...         pass
    >>> class_to_dict_spec(Example)
    ('varargs', 'varkw', {Opt('ann_deflt'): <class 'int'>, 'ann': <class 'str'>, 'pos': None, Opt('kwonly_deflt'): None, Opt('varargs'): None, 'kwonly': None, Opt('varkw'): None})
    '''
    argspec = getfullargspec(cls.__init__)
    newspec = {}
    names = set()
    # types defined by user
    if argspec.annotations:
        for name in argspec.annotations:
            if name not in names and name != 'return' and name != 'self':
                newspec[name] = argspec.annotations[name]
                names.add(name)
    # other args with default are optional
    if argspec.defaults:
        for name in argspec.args[-len(argspec.defaults):]:
            if name not in names:
                newspec[Opt(name)] = None
            else:
                newspec[Opt(name)] = newspec.pop(name)
            names.add(name)
    # other args are required
    if argspec.args:
        for name in argspec.args:
            if name not in names and name != 'self':
                newspec[name] = None
                names.add(name)
    if argspec.kwonlyargs:
        for name in argspec.kwonlyargs:
            if name not in names:
                if argspec.kwonlydefaults and name in argspec.kwonlydefaults:
                    newspec[Opt(name)] = None
                else:
                    newspec[name] = None
                names.add(name)
    # *args and **kargs are optional
    if argspec.varargs and argspec.varargs not in names:
        newspec[Opt(argspec.varargs)] = None
    if argspec.varkw and argspec.varkw not in names:
        newspec[Opt(argspec.varkw)] = None
    return (argspec.varargs, argspec.varkw, newspec)


def checked(func):
    '''
    A decorator that adds **runtime verification of type annotations** to a
    function or method.

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
    @wraps(func)
    def wrapper(*args, **kargs):
        callargs = getcallargs(func, *args, **kargs)
        annotations = dict(getfullargspec(func).annotations)
        rspec = annotations.pop('return', None)
        for name in annotations:
            spec = annotations[name]
            value = callargs.get(name, None)
            verify(spec, value)
        result = func(*args, **kargs)
        verify(rspec, result)
        return result
    return wrapper


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
