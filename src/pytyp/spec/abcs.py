# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and
# limitations under the License.
#
# The Original Code is Pytyp (http://www.acooke.org/pytyp)
# The Initial Developer of the Original Code is Andrew Cooke.
# Portions created by the Initial Developer are Copyright (C) 2011
# Andrew Cooke. All Rights Reserved.
#
# Alternatively, the contents of this file may be used under the terms
# of the LGPL license (the GNU Lesser General Public License,
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions
# of the LGPL License are applicable instead of those above.
#
# If you wish to allow use of your version of this file only under the
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions
# above, a recipient may use your version of this file under either the
# MPL or the LGPL License.

from abc import ABCMeta, abstractmethod
from collections import Sequence, Mapping, ByteString, Container
from itertools import count
from numbers import Number
from reprlib import recursive_repr
from threading import RLock
from weakref import WeakSet, WeakKeyDictionary

from pytyp.util import items, make_recursive_block

# TODO abc_name in wrong place?  see cls
# TODO weak dict for types?


block_recursive_type = make_recursive_block(lambda args: (id(args[0]), id(args[1])), 
                                            lambda _: RecursiveType.throw())


class TSMeta(ABCMeta):
    '''
    The metaclass for type specifications.  This extends ``ABCMeta`` to include 
    the instance hook and adds a few utilities.
    
        >>> normalize(Rec(a=int))
        Rec(a=int)
        >>> normalize({'a': int})
        Rec(a=int)
        >>> normalize((int, str))
        Rec(int,str)
        >>> normalize(Rec((int,), {'a':str}))
        Rec(Rec(int),Rec(a=str))
        >>> normalize([int])
        Seq(int)
        >>> normalize([])
        Seq(Cls(object))
        >>> Seq([int])
        Seq(Seq(int))
        >>> normalize(int)
        int
        >>> class Foo: pass
        >>> normalize(Foo)
        Cls(Foo)
        >>> normalize(Alt(int, str))
        Alt(int,str)
        >>> normalize(Alt(int, Foo))
        Alt(int,Cls(Foo))
        >>> normalize(Opt([int]))
        Opt(Seq(int))
        >>> normalize([int, str])
        Rec(int,str)
    '''
    
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
        This rewrites the "shorthand" form (without ``Cls()``, using ``[]`` 
        instead of ``Seq()``, etc).
        '''
        if isinstance(spec, list):
            if not spec:
                return Seq()
            if len(spec) == 1:
                return Seq(normalize(spec[0]))
            else:
                return Rec(*map(normalize, spec))
        elif isinstance(spec, dict):
            return Rec(_dict=dict((name, normalize(spec[name]))
                                  for name in spec))
        elif isinstance(spec, tuple):
            return Rec(*tuple(normalize(s) for s in spec))
        elif isinstance(spec, type):
            if issubclass(spec, Delayed):
                spec._spec = normalize(spec._spec)
                return spec
            elif NoNormalize in spec.__bases__:
                return spec
            else:
                return Cls(spec)
        else:
            return normalize(type(spec))

    @recursive_repr()
    def __repr__(cls):
        try:
            return cls._reprhook()
        except AttributeError:
            return super().__repr__()

    __str__ = __repr__
        
normalize = TSMeta._normalize
'''
Type specifications are built using constructors like ``Seq()`` and ``Rec()``,
but it is also possible to use a "shorthand" form, in which ``()`` and ``{}`` 
are used for for records, and ``[]`` for sequences.

This routine rewrites the shorthand into the standard format. 
        
    >>> normalize({'a': int})
    Rec(a=int)
    >>> normalize((int, str))
    Rec(int,str)
    >>> normalize([int])
    Seq(int)
    >>> normalize([])
    Seq(Cls(object))
    >>> normalize(Opt([int]))
    Opt(Seq(int))
    >>> normalize([int, str])
    Rec(int,str)
'''
            
    
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
    def _structuralcheck(cls, instance, check=isinstance):
        def verify(_, vsn):
            for (v, s, _) in vsn:
                if not check(v, s): raise TypeError
            return True
        try:
            return cls._backtrack(instance, verify)
        except TypeError:
            return False
    
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

class NoBacktrack(Exception, metaclass=ABCMeta):
    '''
    If this exception (or a subclass, or a registered class) occurs within
    ``_backtrack()`` then it will be allowed to "escape" to the surrounding
    code (other exceptions will be caught and used to trigger backtracking
    over sum types).
    '''
    pass


def expand(value, spec, callback):
    return normalize(spec)._for_each(value, callback)
    
    
def type_error(value, spec):
    raise TypeError('Type {1} inconsistent with {0!r}.'.format(value, spec))


def _hashable_types(args, kargs):
    '''
    Given a list of args and kargs, both of which are type specifications,
    generate a tuple of that information that is sorted so that it can be used as
    a reliable key for the same information (ie normalized and ordered).
    
    Also, order the args (indexed specs) before the kargs so that generating 
    the repr can handle them correctly.
    '''
    types = dict((name, normalize(karg)) for (name, karg) in kargs.items())
    for (index, arg) in zip(count(), args):
        types[index] = normalize(arg)
    return tuple((key, types[key]) for key in sorted(types.keys(), key=str))


def _unhashable_types(types):
    return (tuple(spec for (name, spec) in types if isinstance(name, int)),
            dict((name, spec) for (name, spec) in types if not isinstance(name, int)))
        

def _polymorphic_subclass(bases, args, kargs):
    abc = bases[0]
    args = tuple(normalize(arg) for arg in args)
    kargs = dict((name, normalize(karg)) 
                 for (name, karg) in kargs.items())
    types = _hashable_types(args, kargs)

    with abc._abc_polymorphic_cache_lock:
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
    def _backtrack(cls, value, callback):
        return callback(cls, cls._vsn(value))


class Sum:
    
    @classmethod
    def _backtrack(cls, value, callback):
        for (v, s, n) in cls._vsn(value):
            try:
                return callback(cls, [(v, s, n)])
            except Exception as e:
                if isinstance(e, NoBacktrack): raise
        raise TypeError('No alternative for {}'.format(cls))
    

class Seq(Product):
    '''
    This describes a sequence of values, all of the same type.  For example:
    
        >>> isinstance([1,2,3], Seq(int))
        True
        >>> isinstance(('four', 'five'), Seq(str))
        True
        >>> isinstance([1,'two',None], Seq(int))
        False
    
    If no type is given, then ``object`` is assumed (which is the same as "anything"):
    
        >>> isinstance([1,'two',None], Seq())
        True
    '''

    _abc_polymorphic_cache_lock = RLock()
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
            return super().__new__(cls)

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


class FmtArgsMixin:
    
    @classmethod
    def _fmt_args(cls):
        def args():
            count = 0
            for (name, spec) in cls._abc_type_arguments:
                if name == count and count > -1:
                    count += 1
                    yield str(spec)
                else:
                    count = -1
                    yield '{0}={1}'.format(name, spec)
        return ','.join(args())

    
class Rec(Product, FmtArgsMixin):
    '''
    This describes `records` - containers with contents that are accessed via a name.
    Usually the name is a string:
    
        >>> isinstance({'a':1, 'b':'two'}, Rec(a=int, b=str))
        True
    
    But it can also be an integer (unnamed arguments to ``Rec()`` are numbered from 0):
    
        >>> isinstance((1, 'two'), Rec(int, str))
        True
    
    Or even arbitrary objects:
    
        >>> foo = object()
        >>> isinstance({foo: 1}, Rec(_dict={foo: int}))
        True
    '''

    _abc_polymorphic_cache_lock = RLock()
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
            if not args and not kargs: kargs = {'__': ANY}
            # careful to use normalised form here
            kargs = dict((Rec.OptKey.pack(name), arg) for (name, arg) in kargs.items())
            spec = _polymorphic_subclass((cls, Container), args, kargs)
            if args or kargs != {Rec.OptKey(''):ANY}:
                Rec().register(spec)
            return spec
        else:
            return super().__new__(cls)
        
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
    def _to_dict(cls):
        return dict(cls._abc_type_arguments)

    @classmethod
    def _int_keys(cls):
        for (name, _) in cls._abc_type_arguments:
            if not isinstance(Rec.OptKey.unpack(name), int):
                return False
        return True


class Atr(Product, FmtArgsMixin):
    '''
    This describes the attributes on an object.  Methods are not supported (instead,
    use `function annotations 
    <http://docs.python.org/py3k/reference/compound_stmts.html#index-22>`_ on the 
    method itself::
    
        >>> class Foo:
        ...     def __init__(self, a, b):
        ...         self.a = a
        ...         self.b = b
        >>> foo = Foo(1, 'two')
        >>> Atr(a=int, b=str).register_instance(foo)
        
    The ``Cls()`` constructor (described below) also has a "shorthand" for defining
    classes with attributes:

        >>> class Bar: pass    
        >>> Cls(Bar, a=int, b=str)
        And(Cls(Bar),Atr(a=int,b=str))
    '''

    _abc_polymorphic_cache_lock = RLock()
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
            return super().__new__(cls)

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


class Alt(Sum, FmtArgsMixin):
    '''
    This describes a value that can have more that one type.  For example, 
    ``Alt(int,str)`` can be an ``int`` or a ``str``::
    
        >>> isinstance(1, Alt(number=int, text=str))
        True
        >>> isinstance('two', Alt(number=int, text=str))
        True
        >>> isinstance(3.0, Alt(number=int, text=str))
        False
        
    This is like ``Or()`` below, but lets you add a name to the different
    alternatives (this name is available during iteration - see below - and
    what it means will depend on how the type specification is being used).
    '''
    
    # this makes no sense as a mixin - it exists only to specialise the 
    # functionality provided by the Polymorphic factory above (ie to hold 
    # the cache, provide class methods, etc)

    _abc_polymorphic_cache_lock = RLock()
    _abc_polymorphic_cache = {}
    
    def __new__(cls, *args, **kargs):
        if cls is Alt: # check args only when being used as a class factory
            if (kargs and args) or not (args or kargs):
                raise TypeError('Alt requires named or unnamed arguments, but not both')
            spec = _polymorphic_subclass((cls,), args, kargs)
            return spec
        else:
            return super().__new__(cls)
        
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
        if cls not in (Alt, Opt) and cls._structuralcheck(subclass, check=issubclass):
            return True
        else:
            return NotImplemented

    @classmethod
    def _on(cls, value, **choices):
        for choice in choices:
            for (name, spec) in cls._abc_type_arguments:
                if choice == name and isinstance(value, spec):
                    return choices[choice](value)
        raise TypeError('Cannot dispatch {0} on {1}'.format(value, cls))


class Opt(Alt, NoNormalize):
    '''
    This describes a common case of ``Alt()`` where the value is either the given
    type, or ``None``.
    
        >>> isinstance(1, Opt(int))
        True
        >>> isinstance(None, Opt(int))
        True
        >>> issubclass(Opt(int), Alt(value=int,none=type(None)))
        True
    '''
    
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
            return super().__new__(cls)
            
    @classmethod
    def _fmt_args(cls):
        return cls._abc_type_arguments[1][1]
    

class Cls(Product):
    '''
    This describes a particular class.  You don't need to use it normally (just use
    the class itself), but it is used internally::
    
        >>> Seq(int) is Seq(Cls(int))
        True
    '''
    
    _abc_class_cache = WeakKeyDictionary()
    
    def __new__(cls, class_=object, **kargs):
        if class_ not in cls._abc_class_cache:

            # TODO - convert to call to type with name

            class __Cls(Cls, TypeSpec, NoNormalize):
                
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
        
            cls._abc_class_cache[class_] = __Cls
        spec = cls._abc_class_cache[class_]
        spec._abc_name = Cls.__name__
        if class_ is not object:
            Cls().register(spec)
        if kargs:
            return And(spec, Atr(**kargs))
        else:
            return spec
    
ANY = Cls()
'''
A useful pre-defined type specification that matches any object.  It is the same
as ``Cls(object)`` (which can also be written as ``Cls()``).
'''


class Sub(ReprBase):
    '''
    This is like ``Cls()``, but uses ``issubclass()`` rather than ``isinstance()``.
    
    It doesn't make much sense as a type specification, and is arguably an ugly hack,
    but it is very useful when using :mod:`dispatch by type pytyp.spec.dispatch`.
    '''
          
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
            return super().__new__(cls)
    
    @classmethod
    def transitive_ordered(cls, args):
        '''
        >>> list(And.transitive_ordered([int,And(str,float)]))
        [<class 'float'>, <class 'int'>, <class 'str'>]
        >>> list(And.transitive_ordered([float,And(int,str)]))
        [<class 'float'>, <class 'int'>, <class 'str'>]
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
        # used to sort by id() but it's not fixed, so use str() instead (or tests break)
        return sorted(expand(args, set()), key=str)

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
            return cls._structuralcheck(subclass, check=issubclass) 

    @classmethod
    def _fmt_args(cls):
        return ','.join(str(spec) for (_, spec) in cls._abc_type_arguments)


class And(Product, _Set):
    '''
    This describes something with several different types `at the same time`::
    
        >>> isinstance([1,2,3], And(list, Seq(int)))
        True
        >>> isinstance((1,2,3), And(list, Seq(int)))
        False
        >>> isinstance((1,2,3), Seq(int))
        True
    '''

    _abc_polymorphic_cache_lock = RLock()
    _abc_polymorphic_cache = {}
    
    
class Or(Sum, _Set):
    '''
    This describes something that can is one of several different types (and we
    don't know which).  It is very like ``Alt()`` above, except that the
    alternatives cannot be named.
    
        >>> isinstance(1, Or(int, str))
        True
        >>> isinstance('two', Or(int, str))
        True
        >>> isinstance(3.0, Or(int, str))
        False
    '''

    _abc_polymorphic_cache_lock = RLock()
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
        cls._spec = normalize(spec)
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
