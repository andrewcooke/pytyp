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

from unittest import TestCase
from inspect import formatargspec, getfullargspec

from pytyp._test.support import SimpleArgs, TypedArgs, NamedArgs
from abc import abstractmethod, ABCMeta
from collections import namedtuple


class ReverseTest(TestCase):
    
    def test_argspec(self):
        spec = getfullargspec(TypedArgs.__init__)
        s = formatargspec(*spec)
        assert s == '(self, x: pytyp._test.support.NamedArgs, y: pytyp._test.support.SimpleArgs=None) -> int', s
        ann = spec.annotations
        assert 'x' in ann, ann
        assert ann['x'] == NamedArgs
        assert 'y' in ann, ann
        assert ann['y'] == SimpleArgs
        assert 'return' in ann, ann
        assert ann['return'] == int
        assert len(ann) == 3
        
    def test_abc(self):
        
        class MyAbc(metaclass=ABCMeta):
            @abstractmethod
            def foo(self): pass
            
        class MyExample:
            def foo(self): return 42
            
        assert not isinstance(MyExample(), MyAbc)
        
        MyAbc.register(MyExample)
        assert isinstance(MyExample(), MyAbc)
        
        class MyAbc2(metaclass=ABCMeta):
            @abstractmethod
            def foo(self): pass
        
        class MyExample2:
            def foo(self): return 42
            
        MyAbc2.register(MyExample2)
        assert isinstance(MyExample2(), MyAbc2)
        assert not isinstance(MyExample2(), MyAbc)
        
        MyAbc.register(MyAbc2)
        assert isinstance(MyExample2(), MyAbc) # transitive!
        
        class MyExample3(MyExample2):
            pass
        
        assert isinstance(MyExample3(), MyAbc)
        assert isinstance(MyExample3(), MyAbc2)
        
        class MyAbc4(metaclass=ABCMeta):
            @abstractmethod
            def foo(self): pass
        
        class MyExample4:
            def foo(self): return 42
            
        ex4 = MyExample4()
        try:
            MyAbc4.register(ex4)
            assert False, 'Expected error'
        except TypeError:
            pass
        

    def test_named_tuples(self):
        NT = namedtuple('NT', 'a, b')
        nt = NT(1, 'twp')
        assert nt.a == 1
        try:
            namedtuple('NT', 'a:int, b:str')
            assert False, 'Expected error'
        except ValueError:
            pass
        
        
def mustbe(n):
    def decorator(f):
        def wrapper(self, x):
            if x != n:
                raise ValueError
            return f(self, x)
        return wrapper
    return decorator


class Decorated():
    
    @mustbe(2)
    def __init__(self, value):
        self.value = value
        

class DecoratorTest(TestCase):
    
    def test_decorator(self):
        d = Decorated(2)
        assert d.value == 2
        try:
            Decorated(1)
            assert False, 'Expected error'
        except ValueError:
            pass
        