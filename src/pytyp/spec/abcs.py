
from abc import ABCMeta
from collections import Sequence, Mapping, ByteString, MutableSequence, MutableMapping
from itertools import count
from numbers import Number
from time import time
from weakref import WeakSet, WeakKeyDictionary


class Atomic(metaclass=ABCMeta): pass

Atomic.register(Number)
Atomic.register(ByteString)
Atomic.register(str)
Atomic.register(bool)


def normalize(spec):
    '''
    >>> format(normalize(Map(a=int)))
    'Map(a=int)'
    >>> format(normalize({'a': int}))
    'Map(a=int)'
    >>> format(normalize((int, str)))
    'Map(0=int,1=str)'
    >>> format(normalize(Map((int,), {'a':str})))
    'Map(0=Map(0=int),1=Map(a=str))'
    >>> format(normalize([int]))
    'Seq(int)'
    >>> format(normalize([]))
    'Seq'
    >>> format(normalize(Seq([int])))
    'Seq(Seq(int))'
    >>> format(normalize(int))
    'int'
    >>> class Foo: pass
    >>> format(normalize(Foo))
    'Cls(Foo)'
    >>> format(normalize(Cls(Foo,int)))
    'Cls(Foo,0=int)'
    >>> format(normalize(Alt(int, str)))
    'Alt(0=int,1=str)'
    >>> format(normalize(Alt(int, Foo)))
    'Alt(0=int,1=Cls(Foo))'
    >>> format(normalize(Opt([int])))
    'Opt(Seq(int))'
    '''
    if isinstance(spec, Delayed):
        spec = spec.spec
    if spec is None:
        spec = type(None)
    elif isinstance(spec, list):
        if len(spec) == 1:
            return Seq(normalize(spec[0]))
        elif len(spec) == 0:
            return Seq
        else:
            raise TypeError('List specification should contain at most one value: {0}'.format(spec))
    elif isinstance(spec, dict):
        return Map(**dict((name, normalize(spec[name])) for name in spec))
    elif isinstance(spec, tuple):
        return Map(*tuple(normalize(s) for s in spec))
    elif isinstance(spec, type) and issubclass(spec, Atomic):
        return spec
    try:
        return spec._normalize(normalize)
    except AttributeError:
        if isinstance(spec, type):
            return Cls(spec)
        else:
            return spec # literal value (eg None)


def format(spec):
    try:
        return spec._repr()
    except AttributeError:
        return spec.__name__
    
    
def _hashable_types(*args, **kargs):
    types = dict((name, normalize(karg)) for (name, karg) in kargs.items())
    for (index, arg) in zip(count(), args):
        types[index] = normalize(arg)
    return tuple((key, types[key]) for key in sorted(types.keys()))


def _unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def _polymorphic_subclass(abc, *args, _normalize=None, **kargs):
    if _normalize:
        args = tuple(_normalize(arg) for arg in args)
        kargs = dict((name, _normalize(karg)) for (name, karg) in kargs.items())
    types = _hashable_types(*args, **kargs)
    if types not in abc._abc_polymorphic_cache:
        
        @classmethod
        def register_instance(cls, instance):
            if isinstance(instance, cls):
                return  # Already an instance
            cls._abc_instance_registry.add(instance)
            
        @classmethod
        def __instancehook__(cls, instance):
            try:
                if instance in cls._abc_instance_registry:
                    return True
            except TypeError: # unhashable
                pass
            return cls._structuralcheck(instance)
                
        # replaced a standard class definition with this to help with debugging
        # as it was confusing when everything had the same name
        subclass = type(abc)(abc.__name__ + '_' + str(hash(types)),
                             (abc,),
                             {'_abc_type_arguments': types,
                              '_abc_instance_registry': WeakSet(),
                              'register_instance': register_instance,
                              '__instancehook__': __instancehook__})
                
        abc._abc_polymorphic_cache[types] = subclass
    return abc._abc_polymorphic_cache[types]





class Product:
    
    @staticmethod
    def _verify_contents(vsn):
        try:
#            from functools import reduce
#            from operator import __and__
#            return reduce(__and__, map(lambda x: isinstance(x[0], x[1]), vsn), True)
            for (v, s, _n) in vsn:
                if not isinstance(v, s):
                    return False
            return True
        except TypeError:
            return False
    

class Sum:
    
    @staticmethod
    def _verify_contents(vsn):
        try:
#            from functools import reduce
#            from operator import __or__
#            return reduce(__or__, map(lambda x: isinstance(x[0], x[1]), vsn), False)
            for (v, s, _n) in vsn:
                if isinstance(v, s):
                    return True
            return False
        except TypeError:
            return False


class Seq(Sequence, Product):
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Seq: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Seq requires a single, unnamed argument')
            return _polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Seq, cls).__new__(cls, *args, **kargs)

    @classmethod
    def _expand(cls, instance, callback):
        def vsn():
            try:
                (name, spec) = cls._abc_type_arguments[0]
            except AttributeError:
                (name, spec) = (None, None)
            for value in instance:
                yield (value, spec, name)
        return callback(vsn())
            
    @classmethod
    def _normalize(cls, callback):
        try:
            return Seq(callback(cls._abc_type_arguments[0][1]), _normalize=callback)
        except AttributeError:
            return Seq
        
    @classmethod
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify_contents)
            
    @classmethod
    def _repr(cls):
        try:
            return 'Seq({0})'.format(format(cls._abc_type_arguments[0][1]))
        except AttributeError:
            return 'Seq'


class Map(Mapping, Product):
    
    _abc_polymorphic_cache = {}
    
    class OptKey:
        
        def __init__(self, name):
            self.name = name
            
        @staticmethod
        def unpack(name):
            if isinstance(name, Map.OptKey):
                return name.name
            else:
                return name

    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Map: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Map requires named or unnamed arguments, but not both')
            return _polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Map, cls).__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            try:
                names = value.keys()
            except AttributeError:
                names = range(len(value))
            if hasattr(cls, '_abc_type_arguments'):
                names = set(names)
                # drop existing and optional names
                for (name, spec) in cls._abc_type_arguments:
                    unpacked = Map.OptKey.unpack(name)
                    try:
                        yield (value[unpacked], spec, unpacked) 
                    except KeyError:
                        if not isinstance(name, Map.OptKey):
                            raise TypeError('Missing value for {0}'.format(name))
                    names.discard(unpacked)
                if names:
                    raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
            else:
                for name in names:
                    yield (value[name], None, name)
        return callback(vsn())
        
    @classmethod
    def _normalize(cls, callback):
        try:
            (args, kargs) = _unhashable_types(cls._abc_type_arguments)
            return Map(*args, **kargs)
        except AttributeError:
            return Map
    
    @classmethod
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify_contents)

    @classmethod
    def _repr(cls):
        try:
            return 'Map({0})'.format(
                        ','.join('{0}={1}'.format(name, format(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Map'


class Alt(Sum, metaclass=ABCMeta):
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            return _polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Alt, cls).__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            if hasattr(cls, '_abc_type_arguments'):
                for (name, spec) in cls._abc_type_arguments:
                    yield (value, spec, name)
            else:
                yield (value, None, None)
            raise TypeError('No alternative for {0}'.format(value))
        return callback(vsn())
        
    @classmethod
    def _normalize(cls, callback):
        try:
            (args, kargs) = _unhashable_types(cls._abc_type_arguments)
            return Alt(*args, **kargs)
        except AttributeError:
            return Alt
    
    @classmethod
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify_contents)

    @classmethod
    def _repr(cls):
        try:
            return 'Alt({0})'.format(
                        ','.join('{0}={1}'.format(name, format(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Alt'


class Opt(Alt):
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Opt: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Opt requires a single, unnamed argument')
            return _polymorphic_subclass(cls, none=type(None), value=args[0], 
                                         _normalize=_normalize)
        else:
            return super(Opt, cls).__new__(cls, *args, **kargs)
            
    @classmethod
    def _repr(cls):
        try:
            return 'Opt({0})'.format(format(cls._abc_type_arguments[1][1]))
        except AttributeError:
            return 'Opt'
    

class _Cls:
    
    def __init__(self):
        self._abc_class_cache = WeakKeyDictionary()
    
    def __call__(self, class_, *args, _normalize=normalize, **kargs):
        if class_ not in self._abc_class_cache:

            class __Cls(Product, metaclass=ABCMeta):
                
                _abc_polymorphic_cache = {}
                _abc_class = class_

                @classmethod
                def _expand(cls, value, callback):
                    def vsn():
                        yield (value, cls._abc_class, None)
                        for (name, spec) in cls._abc_type_arguments:
                            yield (getattr(value, name), spec, name)
                    return callback(vsn())
            
                @classmethod
                def _normalize(cls, callback):
                    (args, kargs) = _unhashable_types(cls._abc_type_arguments)
                    return Cls(cls._abc_class, *args, **kargs)
            
                @classmethod
                def _structuralcheck(cls, instance):
                    return cls._expand(instance, cls._verify_contents)

                @classmethod
                def _repr(cls):
                    return 'Cls({0}{1}{2})'.format(
                                cls._abc_class.__name__, 
                               ',' if cls._abc_type_arguments else '',
                               ','.join('{0}={1}'.format(name, format(spec))
                                        for (name, spec) in cls._abc_type_arguments))
        
            self._abc_class_cache[class_] = __Cls
        return _polymorphic_subclass(self._abc_class_cache[class_], *args, 
                                    _normalize=_normalize, **kargs)
    
Cls = _Cls()

Any = Cls(type)


class Delayed():
    
    def __init__(self):
        self.__spec = None
        self.__defined = False
        
    def __iadd__(self, spec):
        assert not self.__defined, 'Delayed already defined'
        self.__spec = spec
        self.__defined = True
        return self
        
    @property
    def spec(self):
        assert self.__defined, 'Delayed type not defined'
        return self.__spec
    
    
PYTYP_PATCHED = 'pytyp_patched'

if not hasattr(ABCMeta, PYTYP_PATCHED):

    instance_check = ABCMeta.__instancecheck__
    def replacement_instancecheck(cls, instance):
        try:
            result = cls.__instancehook__(instance)
            if result: # if false may still be subclass
                return result
        except AttributeError:
            pass
        return instance_check(cls, instance)

    ABCMeta.__instancecheck__ = replacement_instancecheck
    setattr(ABCMeta, PYTYP_PATCHED, time())

    for s in MutableSequence._abc_registry:
        Seq.register(s)
    for m in MutableMapping._abc_registry:
        Map.register(m)


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
