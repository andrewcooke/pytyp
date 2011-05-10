
from inspect import getcallargs, getfullargspec
from functools import wraps

from pytyp.spec.abcs import type_error, TSMeta


def verify(value, spec):
    spec = TSMeta._normalize(spec)
    if not isinstance(value, spec):
        type_error(value, spec)
        
        
def verify_all(callargs, annotations):
    for name in annotations:
        spec = annotations[name]
        try:
            verify(callargs.get(name), spec)
        except AttributeError:
            pass
    
        
def unpack(func):
    annotations = dict((name, TSMeta._normalize(spec))
                       for (name, spec) in getfullargspec(func).annotations.items())
    try:
        rspec = annotations.pop('return')
        do_return = True
    except KeyError:
        rspec = None
        do_return = False
    return (annotations, do_return, rspec)


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
      TypeError: Type str inconsistent with [1, 2, 3].
      >>> @checked
      ... def bad_len(s:str) -> int:
      ...     return 'wrong'
      >>> bad_len('abc')
      Traceback (most recent call last):
        ...
      TypeError: Type int inconsistent with 'wrong'.
    '''
    (annotations, do_return, rspec) = unpack(func)
    @wraps(func)
    def wrapper(*args, **kargs):
        callargs = getcallargs(func, *args, **kargs)
        verify_all(callargs, annotations)
        result = func(*args, **kargs)
        if do_return:
            verify(result, rspec)
        return result
    return wrapper


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
