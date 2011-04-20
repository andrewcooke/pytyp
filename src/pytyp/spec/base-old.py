#LICENCE

from inspect import getfullargspec
from collections import Iterator
from itertools import count
from reprlib import recursive_repr


class Any:
    '''
    Match any type (can also be specified as `*`).
    
      >>> from pytyp.spec.check import verify
      >>> verify('foo', ...)
      >>> normalize(...)
      Any()
      >>> verify('foo', Any())
    '''
    
    def __eq__(self, other):
        return isinstance(other, Any)
    
    def __hash__(self):
        return hash(self.__class__)
    
    def __str__(self):
        return str(...)
    
    def __repr__(self):
        return 'Any()'


class Modifier():
    '''
    Base class for classes that modify types.
    '''
    
    def __init__(self, spec):
        self.spec = spec
        
    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.spec == self.spec
    
    def __hash__(self):
        return hash(self.__class__) ^ hash(self.spec)
    
    @recursive_repr()
    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self.spec)


class Cls(Modifier):
    '''
    Match a class.  Can also be specified as that class (alone).
    
      >>> from pytyp.spec.check import verify
      >>> verify('foo', str)
      >>> normalize(str)
      Cls(<class 'str'>)
      >>> verify('foo', Cls(str))
      >>> str(Cls(str))
      '<str>'
    '''
    
    def __str__(self):
        return '<{0}>'.format(self.spec.__name__)
    

class Dispatchable(Modifier):
    '''
    Subclasses support dispatching by type:
    
      >>> a = Alt(s=str, i=int)
      >>> d = lambda x: a.on(x, s=lambda s: 'string {0}'.format(s),
      ...                       i=(lambda i: 'int {0}'.format(i)))
      >>> d(1)
      'int 1'
      >>> d('x')
      'string x'
      >>> o = Opt(str)
      >>> d = lambda x: o.on(x, none=lambda _: 'none',
      ...                       value=lambda v: 'string {0}'.format(v))
      >>> d(None)
      'none'
      >>> d('x')
      'string x'
    '''
    
    _marker = object()
    
    def __init__(self, named, spec=_marker):
        spec = named if spec == self._marker else spec 
        super(Dispatchable, self).__init__(spec)
        self.named = named
        
    def on(self, _value, **choices):
        from pytyp.spec.check import verify
        if not self.named:
            raise TypeError('Dispatch only possible on named alternatives')
        for name in choices:
            try:
                verify(_value, self.named[name])
            except:
                continue
            return choices[name](_value)
        raise TypeError('Cannot dispatch {0} on {1}'.format(_value, self))
    

class Opt(Dispatchable):
    '''
    Construct an optional type specification.  This allows values of None
    to be matched.

      >>> from pytyp.spec.check import verify
      >>> verify(1, Opt(int))
      >>> verify(None, Opt(int))
      >>> verify('one', Opt(int))
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: one!:<class 'int'>
      >>> repr(Opt(int))
      "Opt(<class 'int'>)"
      >>> str(Opt(int))
      "<class 'int'>?"
    '''
    
    def __init__(self, spec):
        super(Opt, self).__init__({'none': Cls(type(None)), 'value': spec}, spec)
    
    @recursive_repr()
    def __str__(self):
        return str(self.spec) + '?'

    @staticmethod
    def strip(opt):
        try:
            return opt.spec
        except AttributeError:
            return opt
        
        
class Alt(Dispatchable):
    '''
    Construct an alternate (sum/union) type specification.
    
      >>> from pytyp.spec.check import verify
      >>> verify(1, Alt(int, str))
      >>> verify('two', Alt(int, str))
      >>> verify(3.0, Alt(int, str))
      Traceback (most recent call last):
        ...
      TypeError: No choice in (<class 'int'>, <class 'str'>) for 3.0
      >>> repr(Alt(int, str))
      "Alt(<class 'int'>,<class 'str'>)"
      >>> str(Alt(int, str))
      "(<class 'int'>|<class 'str'>)"
      >>> str(Alt(a=int, b=str))
      "(a:<class 'int'>|b:<class 'str'>)"
    '''
    
    def __init__(self, *args, **kargs):
        if args and kargs:
            raise TypeError('An Alt specification must be either all named, or all not')
        if kargs:
            super(Alt, self).__init__(kargs.values())
            self.named = kargs
        else:
            super(Alt, self).__init__(args)
            self.named = {}
            
    @recursive_repr()
    def __str__(self):
        if self.named:
            return '({0})'.format('|'.join('{0}:{1}'.format(name, self.named[name])
                                           for name in self.named))
        else:
            return '({0})'.format('|'.join(map(str, self.spec)))
        
    @recursive_repr()
    def __repr__(self):
        if self.named:
            return 'Alt({0})'.format(','.join('{0}={1!r}'.format(name, self.named[name])
                                              for name in self.named))
        else:
            return 'Alt({0})'.format(','.join(map(repr, self.spec)))
    
    
class Map(Modifier):
    '''
    Construct a named product (record) type specification.

      >>> from pytyp.spec.check import verify
      >>> verify({'a': 1, 'b': 'one'}, Map(a=int, b=str))
      >>> verify({'a': 1, 'b': 2}, Map(a=int, b=str))
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: 2!:<class 'str'>
      >>> str(Map(a=int, b=str))
      "{a:<class 'int'>, b:<class 'str'>}"
    '''
    
    def __init__(self, *indexed, **named):
        if (indexed and named) or not (indexed or named):
            raise TypeError('Map() requires either named or ordered (indexed) arguments')
        if named:
            spec = named
        else:
            spec = dict((index, indexed[index]) for index in range(len(indexed)))
        super(Map, self).__init__(spec)
    
    def __str__(self):
        return '{{{0}}}'.format(', '.join(
            '{0}:{1}'.format(name, self.spec[name]) for name in self.spec))
        
    def __repr__(self):
        return 'Map({0})'.format(','.join('{0}={1!r}'.format(name, self.spec[name])
                                          for name in self.spec))
    
    
class Seq(Modifier):
    '''
    Construct a typed sequence (equivalent to [], but can be hashed).
    
      >>> from pytyp.spec.check import verify
      >>> verify([1,2,3], Seq(int))
      >>> verify([], Seq(int))
      >>> verify((1,2,3), Seq(int))
      >>> verify((), Seq(int))
      >>> verify(    'bad', Seq(int))
      Traceback (most recent call last):
        ...
      TypeError: Value inconsistent with type: b!:<class 'int'>
      >>> str(Seq(int))
      "[<class 'int'>]"
    '''
    
    @recursive_repr()
    def __str__(self):
        return '[{0}]'.format(self.spec)
        
    @recursive_repr()
    def __repr__(self):
        return 'Seq({0!r})'.format(self.spec)
    
    
class Delayed():
    '''
    A type specification that cannot be defined until later, but is needed 
    now.  When available, set with `+=`.
    
    .. warning::
      Pytyp cannot handle recursion within a single type specification.  This
      class is intended to be used across specifications.  See the functor
      documentation for examples.
    '''
    
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
    
    @recursive_repr()
    def __repr__(self):
        if self.__defined:
            return repr(self.spec)
        else:
            return 'Delayed()'
        
    @recursive_repr()
    def __str__(self):
        if self.__defined:
            return str(self.spec)
        else:
            return '...'
        
    def on(self, value, **choices):
        return self.__spec.on(value, **choices)
        
        
def normalize(spec, known=None):
    '''
      >>> d = Delayed()
      >>> d += int
      >>> normalize(d)
      Cls(<class 'int'>)
      
      >>> normalize(...)
      Any()
      >>> normalize(Any())
      Any()
      
      >>> normalize(Opt(int))
      Opt(Cls(<class 'int'>))
      
      >>> normalize(Alt(int, str))
      Alt(Cls(<class 'int'>),Cls(<class 'str'>))
      >>> normalize(Alt(a=int, b=str))
      Alt(a=Cls(<class 'int'>),b=Cls(<class 'str'>))
      
      >>> normalize([int])
      Seq(Cls(<class 'int'>))
      >>> normalize(Seq(int))
      Seq(Cls(<class 'int'>))
      
      >>> normalize((int, str))
      Map(1=<class 'str'>,0=<class 'int'>)
      >>> normalize(Map(a=int, b=str))
      Map(a=Cls(<class 'int'>),b=Cls(<class 'str'>))
      
      >>> normalize(int)
      Cls(<class 'int'>)
      
      >>> normalize(None)
      Cls(<class 'NoneType'>)
      
      >>> d = Delayed()
      >>> s = Alt(d, Opt(d))
      >>> d += s
      >>> normalize(s)
      Alt(...,Opt(...))
    '''
    
    if not known:
        known = {}
    id_ = id(spec)
    if id_ in known:
        return known[id_]
    else:
        known[id_] = Delayed()
    
    def save(s):
        known[id_] += s  # update any existing users of delayed (recursive types)
        known[id_] = s   # future uses can use directly
        return s
    
    def recurse(s):
        return normalize(s, known)
    
    
    if isinstance(spec, Delayed):
        return save(recurse(spec.spec))
    
    if spec == ... or isinstance(spec, Any):
        return save(Any())
    
    if isinstance(spec, Opt):
        return save(Opt(recurse(spec.spec)))

    if isinstance(spec, Alt):
        if spec.named:
            return save(Alt(**dict((name, recurse(spec.named[name]))
                                   for name in spec.named)))
        else:
            return save(Alt(*(recurse(s) for s in spec.spec)))

    if isinstance(spec, list):
        if len(spec) != 1:
            raise TypeError('Lists must be of a single type '
                            '(not {0})'.format(spec))
        return save(Seq(recurse(spec[0])))

    if isinstance(spec, Seq):
        return save(Seq(recurse(spec.spec)))
    
    if isinstance(spec, tuple):
        return save(Map(**dict(zip(map(str, count()), spec))))
    
    if isinstance(spec, Map):
        return save(Map(**dict((name, recurse(spec.spec[name]))
                               for name in spec.spec)))

    if spec is None:
        spec = type(None)
    if isinstance(spec, type):
        return save(Cls(spec))
    
    if isinstance(spec, Cls):
        return save(spec)

    raise TypeError('Unknown type specification: {0}'.format(spec))

        
def dispatch(value, spec,
             on_single, # f(value, spec) -> value
             on_sequence, # f(value, spec) -> list
             on_record, # f(iter(name, value, spec)) -> iter(name, value)
             coerce_dict_to_class=None, # f(cls, *args, **kargs) -> cls
             loops = None
             ):
    '''
    The core of the type system, this matches a value against a type
    specification and calls the appropriate handler function on success.
    
    `Opt()` and `Alt()` are handled internally (by recursion and 
    try/fail, as needed).

    :param spec: Type specification.
    :param value: Value whose type should match the specification.
    :param on_single: Called when a simple value is found.
    :param on_sequence: Called when a sequence of values are found.
    :param on_record: Called when an ordered set of values are found.
    :param coerce_dict_to_class: Called, if defined, when a class type
                                 specification coincides with a `dict`
                                 value (used for unpacking JSON and 
                                 YAML data).
    :return: The result of evaluating the appropriate handler, given
             `spec` and `value`.
    '''
    if not loops:
        loops = set()
    
    def recurse(v, s):
        unique = (id(v), id(s))
        if unique in loops:
            raise TypeError('Recursive Type')
        else:
            loops.add(unique)
        return dispatch(v, s, on_single, on_sequence, on_record, 
                        coerce_dict_to_class, loops)
    
    if isinstance(spec, Delayed):
        spec = spec.spec
    
    if spec == ... or isinstance(spec, Any):
        return on_single(value, spec if isinstance(spec, Any) else Any())
    
    if isinstance(spec, Opt):
        if value is None:
            return on_single(value, spec)
        else:
            return recurse(value, spec.spec)

    if isinstance(spec, Alt):
        for s in spec.spec:
            try:
                return recurse(value, s)
            except:
                pass
        raise TypeError('No choice in {0} for {1}'.format(spec.spec, value))

    if isinstance(spec, list):
        if len(spec) != 1:
            raise TypeError('Lists must be of a single type '
                            '(not {0})'.format(spec))
        else:
            spec = Seq(spec[0])
    if isinstance(spec, Seq):
        return on_sequence(value, spec)
    
    if isinstance(spec, tuple):
        if isinstance(value, Iterator):
            value = list(value)
        if len(spec) != len(value):
            raise TypeError('Tuples must match input data in length '
                            '({0} does not match {1})'.format(spec, value))
        return tuple(v for (_, v) in on_record(zip(count(), value, spec)))
    
    def dispatch_dict(spec):
        try:
            names = set(value.keys())
        except AttributeError:
            names = set(range(len(value)))
        for name in spec:
            try:
                value[name]
                found = True
            except KeyError:
                found = False
            if not found and not isinstance(name, Opt):
                raise TypeError('Missing value for {0}'.format(name))
            names.discard(Opt.strip(name))
        if names:
            raise TypeError('Additional field(s): {0}'.format(', '.join(names)))
        return dict(on_record((Opt.strip(name), value[Opt.strip(name)], spec[name]) 
                              for name in spec if Opt.strip(name) in value))
    
    if isinstance(spec, Map):
        spec = spec.spec
    if isinstance(spec, dict):
        return dispatch_dict(spec)
    
    if isinstance(spec, Cls):
        spec = spec.spec
    if spec is None:
        spec = type(None)
    if isinstance(spec, type):
        if isinstance(value, spec):
            return on_single(value, spec)
        else:
            if not coerce_dict_to_class or not isinstance(value, dict):
                raise TypeError('Value inconsistent with type: {0}!:{1}'.format(value, spec))
            # if we're here, we have a class spec and a dict value
            (varargs, varkw, dict_spec) = class_to_dict_spec(spec)
            new_value = dispatch_dict(dict_spec)
            args = new_value.pop(varargs, ())
            kargs = new_value.pop(varkw, {})
            kargs.update(new_value)    
            return coerce_dict_to_class(spec, args, kargs)

    raise TypeError('Unexpected spec / value: {0}:{1} / {2}:{3}'.format(
                        spec, type(spec), value, type(value)))


def class_to_dict_spec(cls):
    '''
    Create a type specification for a dict, given a class.  This reads any
    type annotation, adds positional args as required, and adds keyword args
    (with defaults) as optional.
    
    :param cls: The class to encode
    :return: `(varargs, varkw, spec)` where `varargs` is the name of the `*args`
             parameter (or `None`); `varkw` is the name of the `**kargs` 
             parameter (or `None`) and `spec` is the type specification.
    
    >>> class Example():
    ...     def __init__(self, pos, ann:str, ann_deflt:int=42, *varargs, kwonly, kwonly_deflt='value', **varkw):
    ...         pass
    >>> #class_to_dict_spec(Example)
    #('varargs', 'varkw', {Opt('ann_deflt'): <class 'int'>, 'ann': <class 'str'>, 'pos': None, Opt('kwonly_deflt'): None, Opt('varargs'): None, Opt('varkw'): None, 'kwonly': None})
    '''
    argspec = getfullargspec(cls.__init__)
    newspec = {}
    names = set()
    # types defined by user
    if argspec.annotations:
        for name in argspec.annotations:
            if name not in names and name != 'return' and name != 'self':
                newspec[name] = argspec.annotations[name]
                names.add(name)
    # other args with default are optional
    if argspec.defaults:
        for name in argspec.args[-len(argspec.defaults):]:
            if name not in names:
                newspec[Opt(name)] = Any()
            else:
                newspec[Opt(name)] = newspec.pop(name)
            names.add(name)
    # other args are required
    if argspec.args:
        for name in argspec.args:
            if name not in names and name != 'self':
                newspec[name] = Any()
                names.add(name)
    if argspec.kwonlyargs:
        for name in argspec.kwonlyargs:
            if name not in names:
                if argspec.kwonlydefaults and name in argspec.kwonlydefaults:
                    newspec[Opt(name)] = Any()
                else:
                    newspec[name] = Any()
                names.add(name)
    # *args and **kargs are optional
    if argspec.varargs and argspec.varargs not in names:
        newspec[Opt(argspec.varargs)] = Any()
    if argspec.varkw and argspec.varkw not in names:
        newspec[Opt(argspec.varkw)] = Any()
    return (argspec.varargs, argspec.varkw, newspec)


if __name__ == "__main__":
    import doctest
    import pytyp.spec.base # need this to avoid placing classes in __main__
    print(doctest.testmod(pytyp.spec.base))
