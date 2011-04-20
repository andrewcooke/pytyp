
from abc import ABCMeta
from collections import Sequence, Mapping
from itertools import count
from time import time
from weakref import WeakSet, WeakKeyDictionary


PYTYP_PATCHED = 'pytyp_patched'

if not hasattr(ABCMeta, PYTYP_PATCHED):
    original = ABCMeta.__instancecheck__

    def replacement_instancecheck(cls, instance):
        try:
            result = cls.__cls_instancecheck__(instance)
            if result is not None:
                return result
        except AttributeError:
            pass
        return original(cls, instance)

    ABCMeta.__instancecheck__ = replacement_instancecheck
    setattr(ABCMeta, PYTYP_PATCHED, time())
        

def type_factory(cls, *args, **kargs):
    types = dict(kargs)
    for (index, arg) in zip(count(), args):
        types[index] = arg
    # TODO - normalise here?
    # convert to tuple of ordered tuples for repeatable hashing
    types = tuple((key, types[key]) for key in sorted(types.keys()))
    if types not in cls._abc_polymorphic_cache:
        
        class Polymorphic(cls):
            
            _abc_type_arguments = types
            _abc_instance_registry = WeakSet()
            
            @classmethod
            def register_instance(cls, instance):
                if isinstance(instance, cls):
                    return  # Already an instance
                # TODO - do we need to check for circularity? (see abc code)
                cls._abc_instance_registry.add(instance)
                
            @classmethod
            def __cls_instancecheck__(cls, instance):
                try:
                    if instance in cls._abc_instance_registry:
                        return True
                except (TypeError, AttributeError):
                    pass
        
        cls._abc_polymorphic_cache[types] = Polymorphic
    return cls._abc_polymorphic_cache[types]


class Seq(Sequence):
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, **kargs):
        if cls is Seq: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Seq requires a single, unnamed argument')
            return type_factory(cls, *args, **kargs)
        else:
            return super(Seq, cls).__new__(cls, *args, **kargs)
        

class Map(Mapping):
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, **kargs):
        if cls is Map: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Map requires named or unnamed arguments, but not both')
            return type_factory(cls, *args, **kargs)
        else:
            return super(Map, cls).__new__(cls, *args, **kargs)
    

class Alt(metaclass=ABCMeta):
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            return type_factory(cls, *args, **kargs)
        else:
            return super(Alt, cls).__new__(cls, *args, **kargs)
    

class Opt(Alt):
    
    # an alias for Alt
    
    def __new__(cls, *args, **kargs):
        if cls is Opt: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Opt requires a single, unnamed argument')
            return type_factory(Alt, none=None, value=args[0])
        else:
            return super(Opt, cls).__new__(cls, *args, **kargs)
    

class _Cls:
    
    def __init__(self):
        self._abc_class_cache = WeakKeyDictionary()
    
    def __call__(self, class_, *args, **kargs):
        if class_ not in self._abc_class_cache:
            class Cls(metaclass=ABCMeta):
                _abc_polymorphic_cache = {}
                _abc_class = class_
            self._abc_class_cache[class_] = Cls
        return type_factory(self._abc_class_cache[class_], *args, **kargs)

Cls = _Cls()


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
