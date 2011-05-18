#LICENCE

from functools import wraps
from reprlib import get_ident


_BORING = dir(type('dummy', (object,), {}))

def items(obj):
    for name in dir(obj):
        if name not in _BORING:
            yield (name, getattr(obj, name))


def make_recursive_block(make_key=lambda args: id(args[0]), 
                            on_recursion=lambda x: x):

    def recursive_block(function):
    
        running = set()
    
        @wraps(function)
        def wrapper(*args):
            subkey = make_key(args)
            key = (subkey, get_ident())
            if key in running:
                return on_recursion(subkey)
            running.add(key)
            try:
                result = function(*args)
            finally:
                running.discard(key)
            return result
        return wrapper
    
    return recursive_block

