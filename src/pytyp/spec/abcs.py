
from abc import ABCMeta
from collections import Sequence, Mapping, ByteString, MutableSequence, MutableMapping
from functools import wraps
from itertools import count
from numbers import Number
from reprlib import recursive_repr, get_ident
from time import time
from weakref import WeakSet, WeakKeyDictionary


class Atomic(metaclass=ABCMeta): pass

Atomic.register(Number)
Atomic.register(ByteString)
Atomic.register(str)
Atomic.register(bool)


class Normalized(metaclass=ABCMeta): pass
    # must be applied directly!

class RecursiveType(TypeError):
    
    @staticmethod
    def throw(_): raise RecursiveType


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


block_instancehook = make_recursive_block(lambda args: (id(args[0]), id(args[1])), 
                                           lambda _: False)


@make_recursive_block()
def normalize(spec):
    '''
    >>> fmt(normalize(Map(a=int)))
    'Map(a=int)'
    >>> fmt(normalize({'a': int}))
    'Map(a=int)'
    >>> fmt(normalize((int, str)))
    'Map(0=int,1=str)'
    >>> fmt(normalize(Map((int,), {'a':str})))
    'Map(0=Map(0=int),1=Map(a=str))'
    >>> fmt(normalize([int]))
    'Seq(int)'
    >>> fmt(normalize([]))
    'Seq'
    >>> fmt(normalize(Seq([int])))
    'Seq(Seq(int))'
    >>> fmt(normalize(int))
    'int'
    >>> class Foo: pass
    >>> fmt(normalize(Foo))
    'Cls(Foo)'
    >>> fmt(normalize(Cls(Foo,int)))
    'Cls(Foo,0=int)'
    >>> fmt(normalize(Alt(int, str)))
    'Alt(0=int,1=str)'
    >>> fmt(normalize(Alt(int, Foo)))
    'Alt(0=int,1=Cls(Foo))'
    >>> fmt(normalize(Opt([int])))
    'Opt(Seq(int))'
    >>> fmt([int, str])
    'Map(0=int,1=str)'
    '''
    if isinstance(spec, list):
        if not spec:
            return Seq
        if len(spec) == 1:
            return Seq(normalize(spec[0]))
        else:
            return Map(*map(normalize, spec))
    elif isinstance(spec, dict):
        return Map(_dict=dict((name, normalize(spec[name])) for name in spec))
    elif isinstance(spec, tuple):
        return Map(*tuple(normalize(s) for s in spec))
    elif isinstance(spec, type):
        if issubclass(spec, Delayed):
            spec._spec = normalize(spec._spec)
            return spec
        elif issubclass(spec, Atomic):
            return spec
        elif Normalized in spec.__bases__:
            return spec
        else:
            return Cls(spec)
    else:
        return normalize(type(spec))


def fmt(spec):
    try:
        return normalize(spec)._fmt()
    except AttributeError:
        try:
            return spec.__name__
        except AttributeError:
            return repr(spec) # only on bad type
    
    
def expand(value, spec, callback):
    return normalize(spec)._expand(value, callback)
    
    
def type_error(value, spec):
    raise TypeError('Value {0!r} inconsistent with type {1}.'\
                    .format(value, fmt(spec)))
        
        
def _hashable_types(args, kargs):
    types = dict((name, normalize(karg)) for (name, karg) in kargs.items())
    for (index, arg) in zip(count(), args):
        types[index] = normalize(arg)
    return tuple((key, types[key]) for key in sorted(types.keys()))


def _unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def _polymorphic_subclass(abc, args, kargs, _normalize=None):
    if _normalize:
        args = tuple(_normalize(arg) for arg in args)
        kargs = dict((name, _normalize(karg)) for (name, karg) in kargs.items())
    types = _hashable_types(args, kargs)
    if types not in abc._abc_polymorphic_cache:
        
        @classmethod
        def register_instance(cls, instance):
            if isinstance(instance, cls):
                return  # Already an instance
            cls._abc_instance_registry.add(instance)
            
        @classmethod
        @block_instancehook
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
                             (abc, Normalized),
                             {'_abc_type_arguments': types,
                              '_abc_instance_registry': WeakSet(),
                              'register_instance': register_instance,
                              '__instancehook__': __instancehook__})
                
        abc._abc_polymorphic_cache[types] = subclass
    return abc._abc_polymorphic_cache[types]


class Product:
    
    @classmethod
    def _verify(cls, vsn):
        try:
            for (v, s, _) in vsn:
                if not isinstance(v, s):
                    return False
            return True
        except TypeError:
            return False
    

class Sum:
    
    @classmethod
    def _verify(cls, vsn):
        try:
            for (v, s, _) in vsn:
                if isinstance(v, s):
                    return True
        except TypeError:
            pass
        return False
    

class Seq(Sequence, Product, Normalized):
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Seq: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Seq requires a single, unnamed argument')
            return _polymorphic_subclass(cls, args, kargs, _normalize=_normalize)
        else:
            return super(Seq, cls).__new__(cls, *args, **kargs)

    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            try:
                (name, spec) = cls._abc_type_arguments[0]
            except AttributeError:
                (name, spec) = (None, None)
            for v in value:
                yield (v, spec, name)
        return callback(vsn())
            
    @classmethod
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify)
            
    @classmethod
    def _fmt(cls):
        try:
            return 'Seq({0})'.format(fmt(cls._abc_type_arguments[0][1]))
        except AttributeError:
            return 'Seq'


class Map(Mapping, Product, Normalized):
    
    _abc_polymorphic_cache = {}
    
    class OptKey:
        
        def __init__(self, name):
            self.name = name
            
        def __repr__(self):
            return '__' + str(self.name)
            
        @staticmethod
        def unpack(name):
            if isinstance(name, Map.OptKey):
                return name.name
            else:
                return name

        @staticmethod            
        def decode(name):
            try:
                if name.startswith('__'):
                    return Map.OptKey(name[2:])
            except AttributeError:
                pass
            return name
        
        def __eq__(self, other): return '__' + self.name == other
        def __ne__(self, other): return '__' + self.name != other
        def __le__(self, other): return '__' + self.name <= other
        def __ge__(self, other): return '__' + self.name >= other
        def __lt__(self, other): return '__' + self.name < other
        def __gt__(self, other): return '__' + self.name > other
        def __hash__(self): return hash('__' + self.name)
        def __str__(self): return '__' + self.name

    def __new__(cls, *args, _normalize=normalize, _dict=None, **kargs):
        if cls is Map: # check args only when being used as a class factory
            if _dict: kargs.update(_dict) 
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Map requires named or unnamed arguments, but not both')
            kargs = dict((Map.OptKey.decode(name), arg) for (name, arg) in kargs.items())
            return _polymorphic_subclass(cls, args, kargs, _normalize=_normalize)
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
                        yield (value[unpacked], spec, name)
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
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify)

    @classmethod
    def _int_keys(cls):
        for (name, _) in cls._abc_type_arguments:
            if not isinstance(Map.OptKey.unpack(name), int):
                return False
        return True

    @classmethod
    def _fmt(cls):
        try:
            return 'Map({0})'.format(
                        ','.join('{0}={1}'.format(name, fmt(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Map'


class Alt(Sum, Normalized, metaclass=ABCMeta):
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or (not args and not kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            return _polymorphic_subclass(cls, args, kargs, _normalize=_normalize)
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
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify)

    @classmethod
    def _fmt(cls):
        try:
            return 'Alt({0})'.format(
                        ','.join('{0}={1}'.format(name, fmt(spec))
                                 for (name, spec) in cls._abc_type_arguments))
        except AttributeError:
            return 'Alt'

    @classmethod
    def _on(cls, value, **choices):
        for choice in choices:
            for (name, spec) in cls._abc_type_arguments:
                if choice == name and isinstance(value, spec):
                    return choices[choice](value)
        raise TypeError('Cannot dispatch {0} on {1}'.format(value, fmt(cls)))


class Opt(Alt, Normalized):
    
    # defining this as a subclass of Alt, rather than simple function that calls
    # Alt just gives a nicer formatting
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        if cls is Opt: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Opt requires a single, unnamed argument')
            return _polymorphic_subclass(cls, (), {'none':type(None), 'value':args[0]}, 
                                         _normalize=_normalize)
        else:
            return super(Opt, cls).__new__(cls, *args, **kargs)
            
    @classmethod
    def _fmt(cls):
        try:
            return 'Opt({0})'.format(fmt(cls._abc_type_arguments[1][1]))
        except AttributeError:
            return 'Opt'
    

class Cls:
    
    _abc_class_cache = WeakKeyDictionary()
    
    def __new__(cls, class_, *args, _normalize=normalize, **kargs):
        if class_ not in cls._abc_class_cache:

            # TODO - convert to call to type with name

            class __Cls(Cls, Product, Normalized, metaclass=ABCMeta):
                
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
                def _structuralcheck(cls, instance):
                    return cls._expand(instance, cls._verify)

                @classmethod
                def _fmt(cls):
                    return 'Cls({0}{1}{2})'.format(
                                cls._abc_class.__name__, 
                               ',' if cls._abc_type_arguments else '',
                               ','.join('{0}={1}'.format(name, fmt(spec))
                                        for (name, spec) in cls._abc_type_arguments))
        
            cls._abc_class_cache[class_] = __Cls
        return _polymorphic_subclass(cls._abc_class_cache[class_], args, kargs,
                                    _normalize=_normalize)
    
Any = Cls(object)


class Delayed(metaclass=ABCMeta):
    
    _count = 0
    
    def __new__(cls, *args, _normalize=normalize, **kargs):
        cls._count += 1
        return type(cls.__name__ + '_' + str(cls._count),
                    (cls,),
                    {'_spec': None,
                     '_defined': False})
    
    @classmethod
    def set(cls, spec):
        assert not cls._defined, 'Delayed already defined'
        cls._spec = spec
        cls._defined = True
        return cls
    
    @classmethod
    def get(cls):
        assert cls._defined, 'Delayed not defined'
        return cls._spec
    
    @classmethod
    def register(cls, subclass):
        return cls.get().register(subclass)
        
    @classmethod
    def register_instance(cls, instance):
        return cls.get().register_instance(instance)
        
    @classmethod
    @block_instancehook
    def __instancehook__(cls, instance):
        return cls.get().__instancehook__(instance)
        
    @classmethod
    def _expand(cls, value, callback):
        return cls.get()._expand(value, callback)
                    
    @classmethod
    def _structuralcheck(cls, instance):
        return cls.get()._structuralcheck(instance)

    @classmethod
    @recursive_repr()
    def _fmt(cls):
        return 'Delayed({0})'.format(fmt(cls.get()))
    
    @classmethod
    def _on(cls, value, **choices):
        return cls.get()._on(value, **choices)
    
    
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
