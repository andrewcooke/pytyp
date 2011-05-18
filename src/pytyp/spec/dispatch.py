#LICENCE

from collections import OrderedDict
from inspect import getcallargs

from pytyp.spec.check import unpack, verify_all


class DispatchError(TypeError): pass


class Overload:
    
    def __init__(self, default):
        self.__name__ = default.__name__
        if unpack(default)[0]:
            raise DispatchError('Default method {} has type specifications.'
                                .format(default.__name__))
        self._final = None
        self.intercept(default)
        
    def intercept(self, method):
        self._final = self.wrap(method, self._final)
        return self._final
    
    def __get__(self, obj, objtype=None):
        if obj:
            return lambda *args, **kargs: self._final(obj, *args, **kargs)
        else:
            return self
    
    @staticmethod
    def wrap(method, previous):
        annotation = unpack(method)[0]
        def wrapper(obj, *args, **kargs):
            callargs = getcallargs(method, obj, *args, **kargs)
            try:
                verify_all(callargs, annotation)
            except TypeError:
                #print('Failed {} with {} {}'.format(method.__name__, args, kargs))
                if previous:
                    return previous(obj, *args, **kargs)
                else:
                    raise
            wrapper.obj = obj # for previous
            return method(obj, *args, **kargs)
        wrapper.previous = lambda *args, **kargs: previous(wrapper.obj, *args, **kargs)
        return wrapper
    

overload = Overload
