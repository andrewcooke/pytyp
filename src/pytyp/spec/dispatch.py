
from collections import OrderedDict
from inspect import getcallargs

from pytyp.spec.check import unpack, verify_all


class DispatchError(TypeError): pass


class Overload:
    
    def __init__(self, default):
        self.__name__ = default.__name__
        self.__methods = OrderedDict() # map from summary to method
        self.__default = None
        self.intercept(default)
        
    def intercept(self, method):
        (annotations, _, _) = unpack(method)
        summary = tuple(annotations.items())
        if self.__default is None and summary:
            raise DispatchError('Default method {} has type specifications.'
                                .format(method.__name__))
        if summary in self.__methods:
            raise DispatchError('Method {} duplicates {}.'
                                .format(method.__name__, 
                                        self.__methods[summary][1].__name))
        self.__methods[summary] = (annotations, method)
        if self.__default is None:
            self.__default = summary
        else:
            self.__methods.move_to_end(self.__default)
        return self
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self         
        return lambda *args, **kargs: self(obj, *args, **kargs)
    
    def __call__(self, obj, *args, **kargs):
        last_error = None
        for (annotation, method) in self.__methods.values():
            try:
                callargs = getcallargs(method, obj, *args, **kargs)
                verify_all(callargs, annotation)
                return method(obj, *args, **kargs)
            except TypeError as e:
                last_error = e
        error = DispatchError('No match in {} for arguments: {!r}'
                              .format(self.__name__, (args, kargs)))
        if last_error:
            error.__cause__ = last_error
        raise error


overload = Overload
