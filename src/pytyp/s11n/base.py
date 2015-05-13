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

from pprint import pprint
from collections import Mapping, Sequence, Callable
from inspect import getfullargspec

from pytyp.spec.dispatch import overload
from pytyp.spec.abcs import Seq, Sub, Rec, Cls, Opt, Alt, ANY, normalize, Atomic


class DecodeError(TypeError): pass


class ToList:
    
    def to_list(self, map):
        for i in range(len(map)):
            yield map[i]
    

class Item(ToList):
    
    def default(self, value, spec):
        try:
            return spec._backtrack(value, self.collection)
        except AttributeError:
            return value
        
    @overload
    def __call__(self, value, spec):
        return self.default(value, spec)
        
    @__call__.intercept
    def dict(self, value:Mapping, spec:Sub(Cls)):
        if spec._abc_class in (object, dict, list) or issubclass(spec._abc_class, Atomic):
            return self.dict.previous(value, spec)
        else:
            return spec._abc_class(**self.default(value, cls_to_rec(spec)))
    
    @__call__.intercept
    def list(self, value:Sequence, spec:Sub(Cls)):
        if spec._abc_class in (object, dict, list) or issubclass(spec._abc_class, Atomic):
            return self.list.previous(value, spec)
        else:
            return spec._abc_class(*list(self.to_list(self.default(value, cls_to_seq(spec)))))
    

class Collection(ToList):
    
    @overload
    def __call__(self, current, vsn):
        '''
        Default case for non-collections
        '''
        as_list = list(vsn)
        assert len(as_list) == 1, 'Too much data for {}'.format(current)
        (v, s, _) = as_list[0]
        return self.item(v, s)
    
    @__call__.intercept
    def rec(self, current:Sub(Rec), vsn):
        map = dict((Rec.OptKey.unpack(n), self.item(v, s)) for (v, s, n) in vsn)
        if current._int_keys(): # tuple if numbered keys
            return tuple(self.to_list(map))
        else:
            return map
    
    @__call__.intercept
    def seq(self, current:Sub(Seq), vsn):
        return list(self.item(v, s) for (v, s, _) in vsn)


def decode(data, spec):
    '''
    Rewrite the given data so that it conforms to the type specification.
    '''
    # construct mutually recursive pair
    collection, item = Collection(), Item()
    collection.item, item.collection = item, collection
    return item(data, normalize(spec))


class ClsConverter:
    
    def __call__(self, cls):
        try:
            init = cls._abc_class.__init__
            while hasattr(init, '__wrapped__'): init = init.__wrapped__
            argspec = getfullargspec(init)
        except TypeError:
            raise DecodeError('{} is not a user-defined class'.format(cls._abc_class))
        self._newspec = {}
        names = set()
        if argspec.args: self.args(argspec, names)
        if argspec.annotations: self.annotations(argspec, names)
        if argspec.defaults: self.defaults(argspec, names)
        if argspec.kwonlyargs: self.kwonlyargs(argspec, names)
        if argspec.varargs: self.varargs(argspec, names)
        if argspec.varkw: self.varkw(argspec, names)
        return Rec(_dict=self._newspec)
    
    def add(self, key, spec):
        name = Rec.OptKey.unpack(key)
        if key in self._newspec:
            assert self._newspec[key] == ANY, 'Already specific'
            self._newspec[key] = spec
        elif name in self._newspec:
            # don't check here - could be making specific value optional
            #assert self._newspec[name] == ANY, 'Already specific'
            del self._newspec[name]
            self._newspec[key] = spec
        else:
            self._newspec[key] = spec
        
    def make_optional(self, key):
        assert key in self._newspec, 'Missing default'
        self.add(Rec.OptKey(key), self._newspec[key])
    
    def update(self, spec):
        self._newspec.update(spec._to_dict())
        
    def arg_name(self, name):
        return name not in ('return', 'self')

    def args(self, argspec, names):
        for name in argspec.args:
            if self.arg_name(name):
                self.add(name, ANY)
                names.add(name)
                
    def annotations(self, argspec, names):
        for name in argspec.annotations:
            if self.arg_name(name) and name not in (argspec.varargs, argspec.varkw):
                self.add(name, normalize(argspec.annotations[name]))
                names.add(name)

    def defaults(self, argspec, names):
        for name in argspec.args[-len(argspec.defaults):]:
            self.make_optional(name)
            
    def kwonlyargs(self, argspec, names):
        for name in argspec.kwonlyargs:
            if name not in names:
                if argspec.kwonlydefaults and name in argspec.kwonlydefaults:
                    self.add(Rec.OptKey(name), ANY)
                else:
                    self.add(name, ANY)
                names.add(name)
                
    def varargs(self, argspec, names):
        if argspec.varargs in argspec.annotations:
            oldspec = normalize(argspec.annotations[argspec.varargs])
            if issubclass(oldspec, Seq):
                self.add(Rec.OptKey(''), oldspec._abc_type_arguments[0][1])
            else:
                raise DecodeError('*args specification was not Seq()')
        else:
            self.add(Rec.OptKey(''), ANY)
    
    def varkw(self, argspec, names):
        if argspec.varkw in argspec.annotations:
            oldspec = normalize(argspec.annotations[argspec.varkw])
            if issubclass(oldspec, Rec):
                self.update(oldspec)
            else:
                raise DecodeError('**kargs specification was not Rec()')
        else:
            self.add(Rec.OptKey(''), ANY)
            
            
class RecConverter(ClsConverter):
    
        def varargs(self, argspec, names):
            raise DecodeError('*args unsupported for map')

cls_to_rec = RecConverter()


class SeqConverter(ClsConverter):
    '''
    The name is a little misleading here.  This generates a Rec() specification
    with integer indices (0, 1, ...) that is used to describe the *args for
    the given class constructor.
    '''
    
    def __call__(self, cls):
        self._count = 0
        self._index = {}
        return super().__call__(cls)
    
    def varkw(self, argspec, names):
        raise DecodeError('**kargs unsupported for list')

    def add(self, key, spec):
        name = Rec.OptKey.unpack(key)
        if name:
            if name not in self._index:
                self._index[name] = self._count
                self._count += 1
            index = self._index[name]
            if index in self._newspec: del self._newspec[index]
            if Rec.OptKey(index) in self._newspec: del self._newspec[Rec.OptKey(index)]
            if name == key: key = index
            else: key = Rec.OptKey(index)
            self._newspec[key] = spec
        else:
            self._newspec[key] = spec
    
    def make_optional(self, key):
        assert key in self._index, 'Missing default'
        self.add(Rec.OptKey(key), self._newspec[self._index[key]])

cls_to_seq = SeqConverter()


class EncodeError(TypeError): pass


class Encoder:
    '''
    An instance of this class can be called to encode data::

      >>> class MyClass:
      ...    def __init__(self, arg1, arg2):
      ...        self.arg1 = arg1
      ...        self.arg2 = arg2
      ...
      >>> myInstance = MyClass(42, 'foo')
      >>> encode = Encoder()
      >>> # use pprint to sort dicts for consistency
      >>> pprint(encode([1,myInstance,{'a':2}]))
      [1, {'arg1': 42, 'arg2': 'foo'}, {'a': 2}]
      
    :param recurse: Should included values also be encoded?  This depends on the
                    requirements of the calling code (JSON and YAML differ).
                    
    :param strict: If true, raise an error if "special" attributes (corresponding
                   to *args etc) are missing.
                   
    :param check_circular: If true, detect and abort on encoding circular data
                           structures.
    '''
    
    def __init__(self, recurse=True, strict=True, check_circular=True):
        self._recurse = recurse
        self._strict = strict
        self._check_circular = check_circular
        self._check = set()
        
    def recurse(self, value):
        if not self._recurse:
            return value
        elif id(value) in self._check:
            raise EncodeError('Circular data: {}'.format(value))
        else:
            if self._check_circular:
                self._check.add(id(value))
            try:
                return self(value)
            finally:
                if self._check_circular:
                    self._check.remove(id(value))
        
    @overload    
    def __call__(self, value):
        return value
    
    @__call__.intercept
    def object(self, value):
        try:
            init = value.__class__.__init__
            while hasattr(init, '__wrapped__'): init = init.__wrapped__
            argspec = getfullargspec(init)
        except TypeError:
            return self.object.previous(value)
        if argspec.varargs and (argspec.varkw or argspec.kwonlyargs):
            try:
                name = value.__class__.__name__
            except:
                name = type(value)
            raise EncodeError('Cannot encode {} - has both *args and **kargs'.format(name))
        elif argspec.varargs:
            return self.seq(value, argspec)
        else:
            return self.rec(value, argspec)
    
    @__call__.intercept
    def list(self, value:Sequence):
        return list(map(self.recurse, value))
    
    @__call__.intercept
    def map(self, value:Mapping):
        return dict((name, self.recurse(value)) for (name, value) in value.items())
    
    @__call__.intercept
    def atomic(self, value:Cls(Atomic)):
        return value
    
    def rec(self, value, argspec):
        
        def check(name, eq, type_):
            val = getattr(value, name)
            if isinstance(val, type_) != eq:
                raise TypeError('{0} for {1} is {2}of type {3}'.format(
                        name, type(val), '' if eq else 'not ', type_))
            return (name, self.recurse(val))
    
        def unpack():
            for name in argspec.args[1:]: # skip self
                # reject Callable to catch the common case of methods
                yield check(name, False, Callable)
            try:
                if argspec.varkw:
                    (_, kargs) = check(argspec.varkw, True, dict)
                    for item in kargs.items(): yield item
            except AttributeError:
                if self._strict: raise
            try:
                for name in argspec.kwonlyargs:
                    yield check(name, False, Callable)
            except AttributeError:
                if self._strict: raise
                
        return dict(unpack())
    
    def seq(self, value, argspec):
        
        def check(name, eq, type_):
            val = getattr(value, name)
            if isinstance(val, type_) != eq:
                raise TypeError('{0} for {1} is {2}of type {3}'.format(
                        name, type(val), '' if eq else 'not ', type_))
            return self.recurse(val)
    
        def unpack():
            for name in argspec.args[1:]: # skip self
                # reject Callable to catch the common case of methods
                yield check(name, False, Callable)
            try:
                if argspec.varargs:
                    args = check(argspec.varargs, True, Sequence)
                    for item in args: yield item
            except AttributeError:
                if self._strict: raise
                
        return list(unpack())
    

encode = Encoder()

