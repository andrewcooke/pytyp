#LICENCE


_BORING = dir(type('dummy', (object,), {}))

def items(obj):
    for name in dir(obj):
        if name not in _BORING:
            yield (name, getattr(obj, name))


