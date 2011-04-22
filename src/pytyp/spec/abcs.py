
from abc import ABCMeta
from collections import Sequence, Mapping, ByteString
from itertools import count
from numbers import Number
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


ATOMIC = {Number, ByteString, str}

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
    if isinstance(spec, list):
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
    elif isinstance(spec, type):
        for type_ in ATOMIC:
            if issubclass(spec, type_):
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


def hashable_types(*args, **kargs):
    types = dict(kargs)
    for (index, arg) in zip(count(), args):
        types[index] = arg
    # TODO - normalise here?
    # convert to tuple of ordered tuples for repeatable hashing
    return tuple((key, types[key]) for key in sorted(types.keys()))


def unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def polymorphic_subclass(abc, *args, _normalize=None, **kargs):
    if _normalize:
        args = tuple(_normalize(arg) for arg in args)
        kargs = dict((name, _normalize(karg)) for (name, karg) in kargs.items())
    types = hashable_types(*args, **kargs)
    if types not in abc._abc_polymorphic_cache:
        
        class PolymorphicSubclass(abc):
            
            _abc_type_arguments = types
            _abc_instance_registry = WeakSet()
            
            @classmethod
            def register_instance(cls, instance):
                if isinstance(instance, cls):
                    return  # Already an instance
                cls._abc_instance_registry.add(instance)
                
            @classmethod
            def __cls_instancecheck__(cls, instance):
                try:
                    if instance in cls._abc_instance_registry:
                        return True
                except (TypeError, AttributeError):
                    pass
                
        abc._abc_polymorphic_cache[types] = PolymorphicSubclass
    return abc._abc_polymorphic_cache[types]


class Seq(Sequence):
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Seq: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Seq requires a single, unnamed argument')
            return polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Seq, cls).__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        try:
            return callback.sequence(value, cls._abc_type_arguments[0][1])
        except AttributeError:
            return callback.sequence(value, None)
        
    @classmethod
    def _normalize(cls, callback):
        try:
            return Seq(callback(cls._abc_type_arguments[0][1]), _normalize=callback)
        except AttributeError:
            return Seq
        
    @classmethod
    def _repr(cls):
        try:
            return 'Seq({0})'.format(format(cls._abc_type_arguments[0][1]))
        except AttributeError:
            return 'Seq'


class Map(Mapping):
    
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

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self._
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Map: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Map requires named or unnamed arguments, but not both')
            return polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Map, cls).__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        if hasattr(cls, '_abc_type_arguments'):
            try:
                names = set(value.keys())
            except AttributeError:
                names = set(range(len(value)))
            # drop existing and optional names
            for (name, spec) in cls._abc_type_arguments:
                try:
                    value[Map.OptKey.unpack(name)]
                    found = True
                except KeyError:
                    if isinstance(name, Map.OptKey):
                        name = name.name
                        found = True
                if not found:
                    raise TypeError('Missing value for {0}'.format(name))
                names.discard(name)
            if names:
                raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
            return callback.mapping((Opt.unpack(name), value[Opt.unpack(name)], spec[name]) 
                                    for name in spec if Opt.unpack(name) in value)
        else:
            return callback.maping((name, value[name], None) for name in value) 
        
    @classmethod
    def _normalize(cls, callback):
        try:
            (args, kargs) = unhashable_types(cls._abc_type_arguments)
            return Map(*args, **kargs)
        except AttributeError:
            return Map
    
    @classmethod
    def _repr(cls):
        try:
            return 'Map({0})'.format(
                        ','.join('{0}={1}'.format(name, format(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Map'


class Alt(metaclass=ABCMeta):
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            return polymorphic_subclass(cls, *args, _normalize=_normalize, **kargs)
        else:
            return super(Alt, cls).__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        if hasattr(cls, '_abc_type_arguments'):
            for (name, spec) in cls._abc_type_arguments:
                try:
                    return callback.alternative(name, value, spec)
                except:
                    pass
            raise TypeError('No alternative in {0} for {1}'.format(
                                            cls._abc_type_arguments, value))
        else:
            return callback.alternative(None, value, None)
        
    @classmethod
    def _normalize(cls, callback):
        try:
            (args, kargs) = unhashable_types(cls._abc_type_arguments)
            return Alt(*args, **kargs)
        except AttributeError:
            return Alt
    
    @classmethod
    def _repr(cls):
        try:
            return 'Alt({0})'.format(
                        ','.join('{0}={1}'.format(name, format(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Alt'


class Opt(Alt):
    
    # a specialised Alt - this works because the cache is on Alt
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Opt: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Opt requires a single, unnamed argument')
            return polymorphic_subclass(cls, none=None, value=args[0], 
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

            class __Cls(metaclass=ABCMeta):
                
                _abc_polymorphic_cache = {}
                _abc_class = class_

                @classmethod
                def _expand(cls, value, callback):
                    return callback.class_(cls._abc_class, value, 
                                           cls._abc_type_arguments)
            
                @classmethod
                def _normalize(cls, callback):
                    (args, kargs) = unhashable_types(cls._abc_type_arguments)
                    return Cls(cls._abc_class, *args, **kargs)
            
                @classmethod
                def _repr(cls):
                    return 'Cls({0}{1}{2})'.format(
                                cls._abc_class.__name__, 
                               ',' if cls._abc_type_arguments else '',
                               ','.join('{0}={1}'.format(name, format(spec))
                                        for (name, spec) in cls._abc_type_arguments))
        
            self._abc_class_cache[class_] = __Cls
        return polymorphic_subclass(self._abc_class_cache[class_], *args, 
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
    
    
if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
