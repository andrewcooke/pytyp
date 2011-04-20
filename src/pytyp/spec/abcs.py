
from abc import ABCMeta
from collections import Sequence, Mapping
from itertools import count
from weakref import WeakSet, WeakKeyDictionary


def type_factory(cls, *args, **kargs):
    types = dict(kargs)
    for (index, arg) in zip(count(), args):
        types[index] = arg
    # TODO - normalise here?
    # convert to tuple of ordered tuples for repeatable hashing
    types = tuple((key, types[key]) for key in sorted(types.keys()))
    if types not in cls._abc_polymorphic_cache:
        print('new class')
        
        class Polymorphic(cls):
            
            _abc_type_arguments = types
            _abc_instance_registry = WeakSet()
            
            @classmethod
            def register_instance(cls, instance):
                if isinstance(instance, cls):
                    return  # Already an instance
                # TODO - do we need to check for circularity? (see abc code)
                cls._abc_instance_registry.add(instance)

        def set_instancecheck(polymorphic):
            previous = polymorphic.__class__.__instancecheck__
            def __instancecheck__(cls, instance):
                try:
                    if instance in Polymorphic._abc_instance_registry:
                        print('locally true')
                        return True
                except TypeError:
                    pass
                x = previous(cls, instance)
                print('parent', x)
                return x
            polymorphic.__class__.__instancecheck__ = __instancecheck__
        
        set_instancecheck(Polymorphic)
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
