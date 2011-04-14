
from inspect import getcallargs, getfullargspec
from functools import wraps

from pytyp.spec.base import dispatch


def verify(value, spec):
    '''
    Check a value against a type specification.  Raises an error on failure.
    
    :param spec: A type specification.
    :param value: A value whose type will be verified against `spec`.
    :result: None if the value is verified; otherwise an error will be thrown.

    This uses the same approach as described above: simple types and
    collections work as expected; `None` matches any type; `Opt()` indicates
    an optional value and `Alt()` a choice:

      >>> from pytyp.spec.base import *
      >>> verify('abc', str)
      >>> verify('abc', ...)
      >>> verify('abc', Any())
      >>> verify(None, str)
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: None!:<class 'str'>
      >>> verify(None, Opt(str))
      >>> verify(1, str)
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: 1!:<class 'str'>
      >>> verify(1, Alt(str, int))
      >>> verify('abc', Alt(str, int))

    Dictionaries are typed by name, values are required unless optional:

      >>> verify({'a': 1, 'b': 'two'}, {'a': int, 'b': str})
      >>> verify({'a': 1, 'b': 'two', 'c':3.4}, {'a': int, 'b': str})
      Traceback (most recent call last):
        ...
      TypeError: Additional field(s): c
      >>> verify({'a': 1}, {'a': int, 'b': str})
      Traceback (most recent call last):
        ...
      TypeError: Missing value for b
      >>> verify({'a': 1}, {'a': int, Opt('b'): str})
      >>> verify({'a': 1, 'b': 'two'}, {'a': int, 'b': Alt(str, int)})
      >>> verify({'a': 1, 'b': 2}, {'a': int, 'b': Alt(str, int)})

    Lists match sequences of the same type:

      >>> verify([], [int])
      >>> verify([1], [int])
      >>> verify([1, 2], [int])
      >>> verify((1, 2), [int])
      >>> verify([1, 'two'], [int])
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: two!:<class 'int'>
      >>> verify([1, 'two'], [Alt(int, str)])

    Tuples allow different types, but lengths must match:

      >>> verify([], (int,))
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [])
      >>> verify([1], (int,))
      >>> verify([1, 'two'], (int, str))
      >>> verify((1, 'two'), (int, str))
      >>> verify([1, 'two'], (int,))
      Traceback (most recent call last):
        ...
      TypeError: Tuples must match input data in length ((<class 'int'>,) does not match [1, 'two'])
      >>> verify((1, 2), (int, str))
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: 2!:<class 'str'>
      >>> verify((1, 2), (int, Alt(int, str)))
    '''
    loops = set()
    def once(value, spec):
        unique = (id(value), id(spec))
        if unique in loops:
            raise TypeError('Recursive loop')
        else:
            loops.add(unique)
    dispatch(value, spec,
        on_single=lambda value, spec: None,
        on_sequence=lambda value, spec: [verify(v, spec.spec) for v in value],
        on_record=lambda nvs: ((n, verify(v, s)) for (n, v, s) in nvs),
        coerce_dict_to_class=None)


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
      TypeError: Value inconsistent with type: [1, 2, 3]!:<class 'str'>
      >>> @checked
      ... def bad_len(s:str) -> int:
      ...     return 'wrong'
      >>> bad_len('abc')
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: wrong!:<class 'int'>
    '''
    @wraps(func)
    def wrapper(*args, **kargs):
        callargs = getcallargs(func, *args, **kargs)
        annotations = dict(getfullargspec(func).annotations)
        try:
            rspec = annotations.pop('return')
            do_return = True
        except KeyError:
            do_return = False
        for name in annotations:
            spec = annotations[name]
            try:
                value = callargs.get(name)
                verify(value, spec)
            except AttributeError:
                pass
        result = func(*args, **kargs)
        if do_return:
            verify(result, rspec)
        return result
    return wrapper


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
