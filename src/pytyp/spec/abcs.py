
from abc import ABCMeta, abstractmethod
from collections import Sequence, Mapping, ByteString, MutableSequence, MutableMapping, \
    Container
from functools import wraps
from itertools import count
from numbers import Number
from reprlib import recursive_repr, get_ident
from weakref import WeakSet, WeakKeyDictionary

from pytyp.util import items


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


block_recursive_type = make_recursive_block(lambda args: (id(args[0]), id(args[1])), 
                                            lambda _: RecursiveType.throw())


class TypeSpecMeta(ABCMeta):
    
    def __instancecheck__(cls, instance):
        try:
            # if false may still be subclass
            if cls.__instancehook__(instance): 
                return True
        except AttributeError:
            pass
        return super().__instancecheck__(instance)
    
    @staticmethod
    @make_recursive_block()
    def _normalize(spec):
        '''
        >>> TypeSpecMeta._normalize(Rec(a=int))
        Rec(a=int)
        >>> TypeSpecMeta._normalize({'a': int})
        Rec(a=int)
        >>> TypeSpecMeta._normalize((int, str))
        Rec(0=int,1=str)
        >>> TypeSpecMeta._normalize(Rec((int,), {'a':str}))
        Rec(0=Rec(0=int),1=Rec(a=str))
        >>> TypeSpecMeta._normalize([int])
        Seq(int)
        >>> TypeSpecMeta._normalize([])
        Seq
        >>> Seq([int])
        Seq(Seq(int))
        >>> TypeSpecMeta._normalize(int)
        int
        >>> class Foo: pass
        >>> TypeSpecMeta._normalize(Foo)
        Cls(Foo)
        >>> TypeSpecMeta._normalize(Alt(int, str))
        Alt(0=int,1=str)
        >>> TypeSpecMeta._normalize(Alt(int, Foo))
        Alt(0=int,1=Cls(Foo))
        >>> TypeSpecMeta._normalize(Opt([int]))
        Opt(Seq(int))
        >>> TypeSpecMeta._normalize([int, str])
        Rec(0=int,1=str)
        '''
        if isinstance(spec, list):
            if not spec:
                return Seq()
            if len(spec) == 1:
                return Seq(TypeSpecMeta._normalize(spec[0]))
            else:
                return Rec(*map(TypeSpecMeta._normalize, spec))
        elif isinstance(spec, dict):
            return Rec(_dict=dict((name, TypeSpecMeta._normalize(spec[name])) 
                                  for name in spec))
        elif isinstance(spec, tuple):
            return Rec(*tuple(TypeSpecMeta._normalize(s) for s in spec))
        elif isinstance(spec, type):
            if issubclass(spec, Delayed):
                spec._spec = TypeSpecMeta._normalize(spec._spec)
                return spec
            elif NoNormalize in spec.__bases__:
                return spec
            else:
                return Cls(spec)
        else:
            return TypeSpecMeta._normalize(type(spec))
    
    @recursive_repr()
    def __repr__(cls):
        try:
            return cls._reprhook()
        except AttributeError:
            return super().__repr__()
    
    
class NoStructural():
    '''
    This identifies subclasses of type specifications, which should not need 
    to have structural verification.  It's equivalent to TypeSpec, but avoids
    the ABC registration logic.
    '''
    pass


class NoNormalize():
    '''
    Immediate subclasses are considered to be type specifications and are not
    normalized.
    '''
    pass


class TypeSpec(NoStructural, metaclass=TypeSpecMeta):
    '''
    Subclasses must provide their own cls._abc_instance_registry as a WeakSet.
    '''

    @classmethod
    def _structuralcheck(cls, instance):
        return cls._expand(instance, cls._verify)
    
    @classmethod
    def _reprhook(cls):
        try:
            return '{}({})'.format(cls._abc_name, cls._fmt_args())
        except AttributeError:
            return cls.__name__
    
    @classmethod
    def register_instance(cls, instance):
        if isinstance(instance, cls):
            return  # Already an instance
        cls._abc_instance_registry.add(instance)
        
    @classmethod
    @block_recursive_type
    def __instancehook__(cls, instance):
        try:
            if instance in cls._abc_instance_registry:
                return True
        except TypeError: # unhashable
            pass
        # only do structural check for classes that are not already subclasses
        # or we get confusing results with empty containers (and slower code)
        if not isinstance(instance, NoStructural):
            return cls._structuralcheck(instance)


class Atomic(metaclass=ABCMeta):
    '''
    These are formatted without "Cls(...)".
    '''
    
Atomic.register(Number)
Atomic.register(ByteString)
Atomic.register(str)
Atomic.register(bool)


class RecursiveType(TypeError):
    
    @staticmethod
    def throw(_): raise RecursiveType


class DelayedTypeError(TypeError): pass


def expand(value, spec, callback):
    return TypeSpecMeta._normalize(spec)._expand(value, callback)
    
    
def type_error(value, spec):
    raise TypeError('Type {1} inconsistent with {0!r}.'.format(value, spec))
        
        
def _hashable_types(args, kargs):
    types = dict((name, TypeSpecMeta._normalize(karg)) for (name, karg) in kargs.items())
    for (index, arg) in zip(count(), args):
        types[index] = TypeSpecMeta._normalize(arg)
    return tuple((key, types[key]) for key in sorted(types.keys()))


def _unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def _polymorphic_subclass(abc, args, kargs):
    args = tuple(TypeSpecMeta._normalize(arg) for arg in args)
    kargs = dict((name, TypeSpecMeta._normalize(karg)) 
                 for (name, karg) in kargs.items())
    types = _hashable_types(args, kargs)
    if types not in abc._abc_polymorphic_cache:
        
        # replaced a standard class definition with this to help with debugging
        # as it was confusing when everything had the same name
        subclass = type(abc)(abc.__name__ + '_' + str(abs(hash(types))), 
                             (abc, TypeSpec, NoNormalize),
                             {'_abc_type_arguments': types,
                              '_abc_instance_registry': WeakSet(),
                              '_abc_name': abc.__name__})
                
        abc._abc_polymorphic_cache[types] = subclass
    return abc._abc_polymorphic_cache[types]


class Product:
    
    @classmethod
    def _verify(cls, vsn, check=isinstance):
        try:
            for (v, s, _) in vsn:
                if not check(v, s):
                    return False
            return True
        except TypeError:
            return False
    

class Sum:
    
    @classmethod
    def _verify(cls, vsn, check=isinstance):
        try:
            for (v, s, _) in vsn:
                try:
                    if check(v, s):
                        return True
                except TypeError:
                    pass
        except TypeError:
            pass
        return False
    

class Seq(Product):
    
    _abc_polymorphic_cache = {}
    
    @abstractmethod
    def __getitem__(self, index):
        raise IndexError
    
    def __new__(cls, *args, **kargs):
        if cls is Seq: # check args only when being used as a class factory
            if kargs or len(args) > 1:
                raise TypeError('Seq requires a single, unnamed argument')
            if not args:
                args = (type,)
            spec = _polymorphic_subclass(cls, args, kargs)
            if args[0] is not type:
                Seq().register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)

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
    def _fmt_args(cls):
        return cls._abc_type_arguments[0][1]

    
class Rec(Product):
    
    _abc_polymorphic_cache = {}
    
    class OptKey:
        
        def __init__(self, name):
            self.name = name
            
        def __repr__(self):
            return '__' + str(self.name)
            
        @staticmethod
        def unpack(name):
            if isinstance(name, Rec.OptKey):
                return name.name
            else:
                return name

        @staticmethod            
        def decode(name):
            try:
                if name.startswith('__'):
                    return Rec.OptKey(name[2:])
            except AttributeError:
                pass
            return name
        
        # these are used only for dicts of program arguments
        def __eq__(self, other): return str(self) == str(other)
        def __ne__(self, other): return str(self) != str(other)
        def __le__(self, other): return str(self) <= str(other)
        def __ge__(self, other): return str(self) >= str(other)
        def __lt__(self, other): return str(self) < str(other)
        def __gt__(self, other): return str(self) > str(other)
        def __hash__(self): return hash(str(self))
        def __str__(self): return '__' +  str(self.name)

    @abstractmethod
    def __getitem__(self, index):
        raise IndexError

    def __new__(cls, *args, _dict=None, **kargs):
        if cls is Rec: # check args only when being used as a class factory
            if _dict: kargs.update(_dict) 
            if kargs and args:
                raise TypeError('Map requires named or unnamed arguments, but not both')
            kargs = dict((Rec.OptKey.decode(name), arg) for (name, arg) in kargs.items())
            spec = _polymorphic_subclass(cls, args, kargs)
            if args:
                Rec().register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
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
                    unpacked = Rec.OptKey.unpack(name)
                    try:
                        yield (value[unpacked], spec, name)
                    except KeyError:
                        if not isinstance(name, Rec.OptKey):
                            raise TypeError('Missing value for {0}'.format(name))
                    names.discard(unpacked)
                if names:
                    raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
            else:
                for name in names:
                    yield (value[name], None, name)
        return callback(vsn())
        
    @classmethod
    def _int_keys(cls):
        for (name, _) in cls._abc_type_arguments:
            if not isinstance(Rec.OptKey.unpack(name), int):
                return False
        return True

    @classmethod
    def _fmt_args(cls):
        return','.join('{0}={1}'.format(name, spec)
                       for (name, spec) in cls._abc_type_arguments)


class Atr(Product):
    
    _abc_polymorphic_cache = {}
    
    @abstractmethod
    def __getattr__(self, key):
        raise KeyError

    def __new__(cls, *args, _dict=None, **kargs):
        if cls is Atr: # check args only when being used as a class factory
            if _dict: kargs.update(_dict) 
            if args or not kargs:
                raise TypeError('Atr requires named arguments')
            spec = _polymorphic_subclass(cls, (), kargs)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            if hasattr(cls, '_abc_type_arguments'):
                # drop existing and optional names
                for (name, spec) in cls._abc_type_arguments:
                    try:
                        yield (getattr(value, name), spec, name)
                    except AttributeError:
                        raise TypeError('Missing attribute for {0}'.format(name))
            else:
                for (name, attr) in items(value):
                    yield (attr, None, name)
        return callback(vsn())
        
    @classmethod
    def _fmt_args(cls):
        return ','.join('{0}={1}'.format(name, spec)
                        for (name, spec) in cls._abc_type_arguments)


class Alt(Sum):
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)
    
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or not (args or kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            spec = _polymorphic_subclass(cls, args, kargs)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            if hasattr(cls, '_abc_type_arguments'):
                for (name, spec) in cls._abc_type_arguments:
                    yield (value, spec, name)
            else:
                yield (value, None, None)
            try:
                raise TypeError('No alternative for {0}'.format(value))
            except DelayedTypeError:
                raise TypeError('No alternative'.format(value))
        return callback(vsn())
        
    @classmethod
    def __subclasshook__(cls, subclass):
        if cls not in (Alt, Opt) and \
                cls._expand(subclass, lambda vsn: cls._verify(vsn, check=issubclass)):
            return True
        else:
            return NotImplemented

    @classmethod
    def _fmt_args(cls):
        return ','.join('{0}={1}'.format(name, spec)
                        for (name, spec) in cls._abc_type_arguments)

    @classmethod
    def _on(cls, value, **choices):
        for choice in choices:
            for (name, spec) in cls._abc_type_arguments:
                if choice == name and isinstance(value, spec):
                    return choices[choice](value)
        raise TypeError('Cannot dispatch {0} on {1}'.format(value, cls))


class Opt(Alt, NoNormalize):
    
    # defining this as a subclass of Alt, rather than simple function that calls
    # Alt just gives a nicer formatting
    
    def __new__(cls, *args, **kargs):
        if cls is Opt: # check args only when being used as a class factory
            if kargs or len(args) != 1:
                raise TypeError('Opt requires a single, unnamed argument')
            kargs = {'none':type(None), 'value':args[0]}
            spec = _polymorphic_subclass(cls, (), kargs)
            if args[0] != object:
                Alt(*kargs).register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
            
    @classmethod
    def _fmt_args(cls):
        return cls._abc_type_arguments[1][1]
    

class Cls:
    
    _abc_class_cache = WeakKeyDictionary()
    
    def __new__(cls, class_=object, **kargs):
        if class_ not in cls._abc_class_cache:

            # TODO - convert to call to type with name

            class __Cls(Cls, TypeSpec, NoNormalize):
                
                _abc_instance_registry = WeakSet()
                _abc_polymorphic_cache = {}
                _abc_class = class_

                @classmethod
                def _expand(cls, value, callback):
                    def vsn():
                        yield (value, cls._abc_class, None)
                    return callback(vsn())

                @classmethod
                def __subclasshook__(cls, subclass):
                    if issubclass(subclass, cls._abc_class):
                        return True
                    else:
                        return NotImplemented

                @classmethod
                def _reprhook(cls):
                    if issubclass(cls._abc_class, Atomic):
                        return cls._abc_class.__name__
                    else:
                        return super()._reprhook()

                @classmethod
                def _fmt_args(cls):
                    return cls._abc_class.__name__
        
            cls._abc_class_cache[class_] = __Cls
        spec = _polymorphic_subclass(cls._abc_class_cache[class_], (), {})
        spec._abc_name = Cls.__name__
        if class_ is not object:
            Cls().register(spec)
        if kargs:
            return And(spec, Atr(**kargs))
        else:
            return spec
    
Any = Cls()


class _Set(TypeSpec):
    
    def __new__(cls, *args, **kargs):
        if _Set in cls.__bases__: # check args only when being used as a class factory
            if kargs or not args:
                raise TypeError('{} requires unnamed arguments'.format(cls.__name__))
            args = cls.transitive_ordered(args)
            abc = _polymorphic_subclass(cls, args, {})
            abc._set_name = cls.__name__
            return abc
        else:
            return super().__new__(cls, *args, **kargs)
    
    @classmethod
    def transitive_ordered(cls, args):
        '''
        >>> list(And.transitive_ordered([int,And(str,float)]))
        [<class 'str'>, <class 'float'>, <class 'int'>]
        >>> list(And.transitive_ordered([float,And(int,str)]))
        [<class 'str'>, <class 'float'>, <class 'int'>]
        '''
        def expand(args, flat):
            for arg in args:
                if isinstance(arg, type) and issubclass(arg, cls) and hasattr(arg, '_abc_type_arguments'):
                    expand((spec for (_, spec) in arg._abc_type_arguments), flat)
                else:
                    try:
                        flat.add(arg._abc_class)
                    except AttributeError:
                        flat.add(arg)
            return flat
        return sorted(expand(args, set()), key=id)

    @classmethod
    def _expand(cls, value, callback):
        def vsn():
            if hasattr(cls, '_abc_type_arguments'):
                # drop existing and optional names
                for (_, spec) in cls._abc_type_arguments:
                    yield (value, spec, None)
            else:
                raise TypeError('Cannot expand {}'.format(cls.__name__))
        return callback(vsn())
        
    @classmethod
    def __subclasshook__(cls, subclass):
        if _Set is cls or _Set in cls.__bases__:
            return NotImplemented
        else:
            return cls._expand(subclass, lambda vsn: cls._verify(vsn, check=issubclass))

    @classmethod
    def _fmt_args(cls):
        return ','.join(spec for (_, spec) in cls._abc_type_arguments)


class And(Product, _Set):
    
    _abc_polymorphic_cache = {}
    
    
class Or(Sum, _Set):

    _abc_polymorphic_cache = {}
    

class Delayed(TypeSpec):
    
    _count = 0
    
    def __new__(cls, *args, **kargs):
        cls._count += 1
        return type(cls.__name__ + '_' + str(cls._count),
                    (cls,),
                    {'_spec': None,
                     '_defined': False,
                     '_abc_name': 'Delayed'})
    
    @classmethod
    def set(cls, spec):
        if cls._defined:
            raise DelayedTypeError('Delayed defined')
        cls._spec = spec
        cls._defined = True
    
    @classmethod
    def get(cls):
        if not cls._defined:
            raise DelayedTypeError('Delayed not defined')
        return cls._spec
    
    @classmethod
    def register(cls, subclass):
        return cls.get().register(subclass)
        
    @classmethod
    def register_instance(cls, instance):
        return cls.get().register_instance(instance)
        
    @classmethod
    @block_recursive_type
    def __instancehook__(cls, instance):
        return cls.get().__instancehook__(instance)
        
    @classmethod
    def _expand(cls, value, callback):
        return cls.get()._expand(value, callback)
                    
    @classmethod
    def _structuralcheck(cls, instance):
        return cls.get()._structuralcheck(instance)

    @classmethod
    def _fmt_args(cls):
        return cls.get()
    
    @classmethod
    def _on(cls, value, **choices):
        return cls.get()._on(value, **choices)


def copy_registry(abc, target):
    for cls in abc._abc_registry:
        target.register(cls)

Container.register(Seq())
copy_registry(Sequence, Seq())
copy_registry(MutableSequence, Seq())
Container.register(Rec())
copy_registry(Mapping, Rec())
copy_registry(MutableMapping, Rec())


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
