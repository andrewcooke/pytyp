
from abc import ABCMeta, abstractmethod
from collections import Sequence, Mapping, ByteString, MutableSequence, MutableMapping, \
    Container
from functools import wraps
from itertools import count
from numbers import Number
from reprlib import recursive_repr, get_ident
from weakref import WeakSet, WeakKeyDictionary

from pytyp.util import items

# TODO abc_name in wrong place?  see cls
# TODO weak dict for types?


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


class TSMeta(ABCMeta):
    
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
        >>> TSMeta._normalize(Rec(a=int))
        Rec(a=int)
        >>> TSMeta._normalize({'a': int})
        Rec(a=int)
        >>> TSMeta._normalize((int, str))
        Rec(0=int,1=str)
        >>> TSMeta._normalize(Rec((int,), {'a':str}))
        Rec(0=Rec(0=int),1=Rec(a=str))
        >>> TSMeta._normalize([int])
        Seq(int)
        >>> TSMeta._normalize([])
        Seq
        >>> Seq([int])
        Seq(Seq(int))
        >>> TSMeta._normalize(int)
        int
        >>> class Foo: pass
        >>> TSMeta._normalize(Foo)
        Ins(Foo)
        >>> TSMeta._normalize(Alt(int, str))
        Alt(0=int,1=str)
        >>> TSMeta._normalize(Alt(int, Foo))
        Alt(0=int,1=Ins(Foo))
        >>> TSMeta._normalize(Opt([int]))
        Opt(Seq(int))
        >>> TSMeta._normalize([int, str])
        Rec(0=int,1=str)
        '''
        if isinstance(spec, list):
            if not spec:
                return Seq()
            if len(spec) == 1:
                return Seq(TSMeta._normalize(spec[0]))
            else:
                return Rec(*map(TSMeta._normalize, spec))
        elif isinstance(spec, dict):
            return Rec(_dict=dict((name, TSMeta._normalize(spec[name])) 
                                  for name in spec))
        elif isinstance(spec, tuple):
            return Rec(*tuple(TSMeta._normalize(s) for s in spec))
        elif isinstance(spec, type):
            if issubclass(spec, Delayed):
                spec._spec = TSMeta._normalize(spec._spec)
                return spec
            elif NoNormalize in spec.__bases__:
                return spec
            else:
                return Ins(spec)
        else:
            return TSMeta._normalize(type(spec))

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


class ReprBase(NoStructural, metaclass=TSMeta):

    @classmethod
    def _reprhook(cls):
        try:
            return '{}({})'.format(cls._abc_name, cls._fmt_args())
        except AttributeError:
            return cls.__name__
    

class TypeSpec(ReprBase):
    '''
    Subclasses must provide their own cls._abc_instance_registry as a WeakSet.
    '''

    @classmethod
    def _structuralcheck(cls, instance):
        return cls._for_each(instance, cls._verify)
    
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
        
    @classmethod
    def _for_each(cls, value, callback):
        return callback(cls, cls._vsn(value))


class Atomic(metaclass=ABCMeta):
    '''
    These are formatted without "Ins(...)".
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
    return TSMeta._normalize(spec)._for_each(value, callback)
    
    
def type_error(value, spec):
    raise TypeError('Type {1} inconsistent with {0!r}.'.format(value, spec))
        
        
def _hashable_types(args, kargs):
    types = dict((name, TSMeta._normalize(karg)) for (name, karg) in kargs.items())
    for (index, arg) in zip(count(), args):
        types[index] = TSMeta._normalize(arg)
    return tuple((key, types[key]) for key in sorted(types.keys()))


def _unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def _polymorphic_subclass(bases, args, kargs):
    abc = bases[0]
    args = tuple(TSMeta._normalize(arg) for arg in args)
    kargs = dict((name, TSMeta._normalize(karg)) 
                 for (name, karg) in kargs.items())
    types = _hashable_types(args, kargs)
    if types not in abc._abc_polymorphic_cache:
        
        # replaced a standard class definition with this to help with debugging
        # as it was confusing when everything had the same name
        subclass = type(abc)(abc.__name__ + '_' + str(abs(hash(types))), 
                             tuple(list(bases) + [TypeSpec, NoNormalize]),
                             {'_abc_type_arguments': types,
                              '_abc_instance_registry': WeakSet(),
                              '_abc_name': abc.__name__})
                
        abc._abc_polymorphic_cache[types] = subclass
    return abc._abc_polymorphic_cache[types]


class Product:
    
    @classmethod
    def _verify(cls, _, vsn, check=isinstance):
        try:
            for (v, s, _) in vsn:
                if not check(v, s):
                    return False
            return True
        except TypeError:
            return False
        
    @classmethod
    def _backtrack(cls, value, callback):
        return callback(cls, cls._vsn(value))
    

class Sum:
    
    @classmethod
    def _verify(cls, _, vsn, check=isinstance):
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
    
    @classmethod
    def _backtrack(cls, value, callback):
        for (v, s, n) in cls._vsn(value):
            try:
                return callback(cls, [(v, s, n)])
            except TypeError:
                pass
        raise TypeError('No alternative for {}'.format(cls))
    

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
                args = (object,)
            spec = _polymorphic_subclass((cls, Sequence), args, kargs)
            if args[0] is not object:
                Seq().register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)

    @classmethod
    def _vsn(cls, value):
        try:
            (name, spec) = cls._abc_type_arguments[0]
        except AttributeError:
            (name, spec) = (None, None)
        for v in value:
            yield (v, spec, name)
            
    @classmethod
    def _fmt_args(cls):
        return cls._abc_type_arguments[0][1]

    
class Rec(Product):
    
    _abc_polymorphic_cache = {}
    
    class OptKey:
        
        def __init__(self, name=''):
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
        def pack(name):
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
            kargs = dict((Rec.OptKey.pack(name), arg) for (name, arg) in kargs.items())
            spec = _polymorphic_subclass((cls, Container), args, kargs)
            if args:
                Rec().register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
    @classmethod
    def _vsn(cls, value):
        try:
            names = value.keys()
        except AttributeError:
            names = range(len(value))
        default = None
        if hasattr(cls, '_abc_type_arguments'):
            names = set(names)
            # drop existing and optional names
            for (name, spec) in cls._abc_type_arguments:
                unpacked = Rec.OptKey.unpack(name)
                if unpacked:
                    try:
                        yield (value[unpacked], spec, name)
                    except KeyError:
                        if not isinstance(name, Rec.OptKey):
                            raise TypeError('Missing value for {0}'.format(name))
                    names.discard(unpacked)
                else:
                    default = spec
            if names:
                if default:
                    for name in names:
                        yield (value[name], default, name)
                else:
                    raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
        else:
            for name in names:
                yield (value[name], None, name)

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
            spec = _polymorphic_subclass((cls,), (), kargs)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
    @classmethod
    def _vsn(cls, value):
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
            spec = _polymorphic_subclass((cls,), args, kargs)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
        
    @classmethod
    def _vsn(cls, value):
        if hasattr(cls, '_abc_type_arguments'):
            for (name, spec) in cls._abc_type_arguments:
                yield (value, spec, name)
        else:
            yield (value, None, None)
        try:
            raise TypeError('No alternative for {0}'.format(value))
        except DelayedTypeError:
            raise TypeError('No alternative'.format(value))

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls not in (Alt, Opt) and \
                cls._for_each(subclass, lambda c, vsn: cls._verify(c, vsn, check=issubclass)):
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
            spec = _polymorphic_subclass((cls,), (), kargs)
            if args[0] != object:
                Alt(*kargs).register(spec)
            return spec
        else:
            return super().__new__(cls, *args, **kargs)
            
    @classmethod
    def _fmt_args(cls):
        return cls._abc_type_arguments[1][1]
    

class Ins(Product):
    
    _abc_class_cache = WeakKeyDictionary()
    
    def __new__(cls, class_=object, **kargs):
        if class_ not in cls._abc_class_cache:

            # TODO - convert to call to type with name

            class __Ins(Ins, TypeSpec, NoNormalize):
                
                _abc_instance_registry = WeakSet()
                _abc_class = class_

                @classmethod
                def _vsn(cls, value):
                    yield (value, cls._abc_class, None)

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
        
            cls._abc_class_cache[class_] = __Ins
        spec = cls._abc_class_cache[class_]
        spec._abc_name = Ins.__name__
        if class_ is not object:
            Ins().register(spec)
        if kargs:
            return And(spec, Atr(**kargs))
        else:
            return spec
    
Any = Ins()


class Sub(ReprBase):
          
    _abc_class_cache = WeakKeyDictionary()
    
    def __new__(cls, spec=object):
        if spec not in cls._abc_class_cache:
            
            class __Sub(Sub, NoNormalize):
                
                _abc_class = spec
                _abc_name = Sub.__name__

                @classmethod
                @block_recursive_type
                def __instancehook__(cls, instance):
                    return issubclass(instance, cls._abc_class)

                @classmethod
                def _fmt_args(cls):
                    return cls._abc_class.__name__
        
            cls._abc_class_cache[spec] = __Sub
        spec = cls._abc_class_cache[spec]
        return spec


class _Set(TypeSpec):
    
    def __new__(cls, *args, **kargs):
        if _Set in cls.__bases__: # check args only when being used as a class factory
            if kargs or not args:
                raise TypeError('{} requires unnamed arguments'.format(cls.__name__))
            args = cls.transitive_ordered(args)
            abc = _polymorphic_subclass((cls,), args, {})
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
    def _vsn(cls, value):
        if hasattr(cls, '_abc_type_arguments'):
            # drop existing and optional names
            for (_, spec) in cls._abc_type_arguments:
                yield (value, spec, None)
        else:
            raise TypeError('Cannot expand {}'.format(cls.__name__))
        
    @classmethod
    def __subclasshook__(cls, subclass):
        if _Set is cls or _Set in cls.__bases__:
            return NotImplemented
        else:
            return cls._for_each(subclass, lambda c, vsn: cls._verify(c, vsn, check=issubclass))

    @classmethod
    def _fmt_args(cls):
        return ','.join(spec for (_, spec) in cls._abc_type_arguments)


class And(Product, _Set):
    
    _abc_polymorphic_cache = {}
    
    
class Or(Sum, _Set):

    _abc_polymorphic_cache = {}
    

class Delayed(TypeSpec, NoNormalize):
    
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
        cls._spec = TSMeta._normalize(spec)
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
    def _vsn(cls, value):
        return cls.get()._vsn(value)
                    
    @classmethod
    def _for_each(cls, value, callback):
        return cls.get()._for_each(value, callback)
                    
    @classmethod
    def _backtrack(cls, value, callback):
        return cls.get()._backtrack(value, callback)
                    
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
    for cls in abc.__subclasses__():
        if cls not in (target, target()):
            target().register(cls)


copy_registry(Sequence, Seq)
Seq().register(tuple)
copy_registry(Mapping, Rec)
Rec().register(tuple)


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
