
from inspect import getcallargs, getfullargspec
from functools import wraps

from pytyp.spec.abcs import fmt, normalize, type_error


def verify(value, spec):
    if not isinstance(value, normalize(spec)):
        type_error(value, spec)


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
      TypeError: Value [1, 2, 3] inconsistent with type str.
      >>> @checked
      ... def bad_len(s:str) -> int:
      ...     return 'wrong'
      >>> bad_len('abc')
      Traceback (most recent call last):
        ...
      TypeError: Value 'wrong' inconsistent with type int.
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
                verify(callargs.get(name), normalize(spec))
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
