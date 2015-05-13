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

from pytyp.spec.check import verify
from pytyp.util import items
from pytyp.spec.abcs import ANY


class TypedValue:
    '''
    Wrap a value with a spec (and verify them).
    '''
    
    def __init__(self, value, spec, verified=True):
        if verified:
            verify(value, spec)
            self.__verified = True
        else:
            self.__verified = False
        self.__value = value
        self.__spec = spec

    @property
    def spec(self):
        return self.__spec
    
    @property
    def value(self):
        if not self.__verified:
            verify(self.__value, self.__spec)
            self.__verified = True
        return self.__value
    
    @value.setter
    def value(self, value):
        verify(value, self.__spec)
        self.__verified = True
        self.__value = value
    
    def __repr__(self):
        return '{0}(value={1!r}, spec={2!r})'.format(
            self.__class__.__name__, self.value, self.spec)
        
    def on(self, **choices):
        return self.__spec.on(self.value, **choices)
    
    def set_on(self, **choices):
        self.value = self.__spec.on(self.value, **choices)
        
    
class TypedProperty:
    
    def __init__(self, *args):
        if not args or len(args) > 2:
            raise TypeError('TypedProperty takes 1 or 2 arguments')
        try:
            self.__value, self.__spec = args
        except ValueError:
            self.__value, self.__spec = (None, args[0])
        self.__name = None
            
    def _install(self, target, name):
        if self.__name:
            assert name == self.__name
        else:
            self.__name = name
        tv = TypedValue(self.__value, self.__spec, verified=False)
        def add(name, method):
            if name.startswith('set_'):
                def setter(*args, **kargs):
                    tv.value = method(tv.value, tv.spec, *args, **kargs)
                tv.__dict__[name] = setter
            else:
                tv.__dict__[name] = \
                    lambda *args, **kargs: method(tv.value, tv.spec, *args, **kargs)
        for (m_name, method) in items(self):
            if not m_name.startswith('_'):
                add(m_name, method)
        target[name] = tv
        
    def __get__(self, instance, type_=None):
        if not instance:
            raise ValueError('Only valid on instance')
        #print('get', self.__name)
        return getattr(getattr(instance, 'p'), self.__name).value
    
    def __set__(self, instance, value):
        if not instance:
            raise ValueError('Only valid on instance')
        #print('set', self.__name, value)
        getattr(getattr(instance, 'p'), self.__name).value = value


class _AsAttributes:
    
    def __init__(self, contents):
        for (name, value) in contents.items():
            setattr(self, name, value)


class Typed:
    '''
    A superclass for objects with typed attributes.
    
      >>> class C(Typed):
      ...     a = TypedProperty(int)
      ...     b = TypedProperty('foo', str)
      ...     def __init__(self):
      ...         super(C, self).__init__()
      ...         self.a = 1
      >>> c = C()
      >>> c.a
      1
      >>> c.b
      'foo'
      >>> c.a = 2
      >>> c.a
      2
      >>> c.b = 2
      Traceback (most recent call last):
        ...
      TypeError: Type str inconsistent with 2.
    '''
    
    def __init__(self):
        p = {}
        for (name, value) in self.__class__.__dict__.items():
            if isinstance(value, TypedProperty):
                value._install(p, name)
        setattr(self, 'p', _AsAttributes(p))


class TypedDict(dict):
    '''
    A class that behaves in the same way as a normal `dict()` except that
    entries can be typed by setting a `TypedValue()`.  Mutation of an 
    existing value checks the type first.  Deleting an entry removes any
    type information.
    
    Since methods otherwise duplicate `dict()` the only way to access the
    type information is through the additional methods `typed_get()` and
    `typed_items()`.
    
      >>> td = TypedDict(a=TypedValue('one', str), b=TypedValue(2, int))
      >>> len(td)
      2
      >>> repr(td)
      "TypedDict([('a', TypedValue(value='one', spec=<class 'str'>)), ('b', TypedValue(value=2, spec=<class 'int'>))])"
      >>> td['a']
      'one'
      >>> td['b']
      2
      >>> td['b'] = 'two'
      Traceback (most recent call last):
        ...
      TypeError: Type int inconsistent with 'two'.
      >>> del td['b']
      >>> td['b'] = 'two'
      >>> td['b'] = 2
      >>> td['b'] = TypedValue('two', str)
      >>> td['b'] = 2
      Traceback (most recent call last):
        ...
      TypeError: Type str inconsistent with 2.
    '''

    def __init__(self, *args, **kargs):
        self.update(*args, **kargs)
        
    def update(self, *args, **kargs):
        if args:
            if len(args) > 1:
                raise TypeError('update takes at most 1 positional argument')
            other = args[0]
            try:
                for (name, value) in other.typed_items():
                    self[name] = value
            except AttributeError:
                try:
                    for name in other.keys():
                        self[name] = other[name]
                except AttributeError:
                    for (name, value) in other:
                        self[name] = value
        for name in kargs:
            self[name] = kargs[name]
            
    def __getitem__(self, name):
        if name in self:
            return super(TypedDict, self).__getitem__(name).value
        else:
            raise KeyError(name)

    def __setitem__(self, name, value):
        if isinstance(value, TypedValue):
            super(TypedDict, self).__setitem__(name, value)
        else:
            spec = self.typed_get(name).spec if name in self else ANY
            super(TypedDict, self).__setitem__(name, TypedValue(value, spec))

    def values(self):
        for value in super(TypedDict, self).values():
            yield value.value

    def items(self):
        for name in self.keys():
            yield (name, self[name])
            
    def typed_items(self):
        return super(TypedDict, self).items()

    __marker = object()

    def pop(self, name, default=__marker):
        if name in self:
            try:
                return self[name]
            finally:
                del self[name]
        elif default != self.__marker:
            return default
        else:
            raise KeyError(name)

    def get(self, name, default=__marker):
        if name in self:
            return self[name]
        elif default != self.__marker:
            return default
        else:
            raise KeyError(name)

    def typed_get(self, name, default=__marker):
        if name in self:
            return super(TypedDict, self).get(name)
        elif default != self.__marker:
            return default
        else:
            raise KeyError(name)

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, sorted(list(self.typed_items()), key=str))


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
