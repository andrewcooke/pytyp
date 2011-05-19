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

from collections import Sequence, Mapping, MutableMapping
from functools import reduce
from itertools import count
from operator import __and__
from unittest import TestCase

from pytyp.spec.abcs import Seq, Rec, Alt, Opt, Cls, ANY, Delayed, And, Atr, Or,\
    Product, Sum, Sub, NoNormalize, TSMeta
from pytyp.spec.dispatch import overload


class SeqTest(TestCase):
    
    def test_simple(self):
        sint = Seq(int) 
        assert isinstance(sint, type)
        
    def test_cached(self):
        sint1 = Seq(int)
        sint2 = Seq(int)
        assert sint1 is sint2
        
    def test_not_cached(self):
        sint = Seq(int)
        sfloat = Seq(float)
        assert sint is not sfloat
        assert sint._abc_type_arguments == ((0, Cls(int)),), sint._abc_type_arguments
        
    def test_mixin(self):
        SFloat = Seq(float)
        class Baz(SFloat):
            def __getitem__(self, index):
                return 42
            def __len__(self):
                return 42
        baz = Baz()
        #assert isinstance(baz, Sequence)
        assert isinstance(baz, SFloat)

    def test_list(self):
        class Bar(list, Seq(int)): pass
        bar = Bar([1,2,3])
        assert isinstance(bar, Seq(int))
        assert isinstance(bar, Sequence)
        assert isinstance(bar, list)
        assert bar[1:] == [2,3], bar[1:]
        assert not isinstance(bar, Seq(float))
        
        assert issubclass(Bar, Seq)
        assert not issubclass(Bar, Seq(str))
        assert issubclass(Bar, Seq(int))

    def test_subclass(self):
        class Boo(list, Seq):
            def __getitem__(self, index):
                return 42
            def __len__(self):
                return 42
        boo = Boo([1,2,3])
        assert isinstance(boo, Sequence)
        
    def test_args(self):
        try:
            Seq(int, float)
            assert False, 'Expected error'
        except TypeError as e:
            assert 'single' in str(e)

    def test_for_docs(self):
        class Bar(list, Seq(int)): pass
        bar = Bar([1,2,3])
        assert isinstance(bar, Seq(int))
        assert isinstance(bar, Seq)
        assert isinstance(bar, Sequence)
        assert isinstance(bar, list)
        assert bar[1:] == [2,3], bar[1:]
        assert not isinstance(bar, Seq(float))
        class Boo(Seq):
            def __init__(self, *l):
                self.__list = list(l)
            def __getitem__(self, index):
                return self.__list.__getitem__(index)
            def __len__(self):
                return len(self.__list)
        boo = Boo(1,'two', 3.0)
        assert boo[1:] == ['two', 3.0]
        assert isinstance(boo, Seq)
        #assert isinstance(boo, Sequence)
        assert not isinstance(boo, Seq(int))
        
    def test_is_subclass(self):
        assert issubclass(list, Sequence)
        assert issubclass(list, Seq())
        assert not issubclass(list, Seq(int))
        assert issubclass(tuple, Sequence)
        assert issubclass(tuple, Seq())
        assert not issubclass(dict, Sequence)
        assert not issubclass(dict, Seq())

    def test_register(self):
        class Foo: pass
        foo = Foo()
        assert not isinstance(foo, Seq(int))
        Seq(int).register_instance(foo)
        assert isinstance(foo, Seq(int))
        
        assert not issubclass(Foo, Seq(int))
        Seq(int).register(Foo)
        assert not issubclass(Foo, Seq(str))
        assert issubclass(Foo, Seq(int))
        assert issubclass(Foo, Seq())
        
    def test_seq_structural(self):
        assert isinstance([1,2,3], Seq(int))
        assert not isinstance(1, Seq(int))
        assert not isinstance([1,'two'], Seq(int))
        assert isinstance([1, None], Seq(Opt(int)))
        assert isinstance([1, None, 'three'], Seq(ANY))
        
    def test_loop(self):
        d = Delayed()
        d2 = Alt(int, d, str)
        d.set(d2)
        assert repr(d) == 'Delayed(Alt(int,...,str))', repr(d)
        assert isinstance(1, d)
        assert isinstance('two', d)
        
    def test_untyped(self):
        class MyIntSequence(list, Seq(int)): pass
        ilist = MyIntSequence()
        assert isinstance(ilist, Seq(int))
        assert not isinstance(ilist, Seq(float))
        assert isinstance(ilist, Seq)
        
        
class RecTest(TestCase):
    
    def test_subclass(self):
        class Bar(dict, Rec(a=int, b=str)): pass
        bar = Bar({'a':1, 'b':'two'})
        assert bar['a'] == 1
        assert isinstance(bar, Rec(a=int, b=str))
        assert not isinstance(bar, Rec(a=int, b=int))
        assert isinstance({}, Rec())
        
        assert issubclass(Bar, Rec())
        assert not issubclass(Bar, Rec(a=int, b=float))
        assert issubclass(Bar, Rec(a=int, b=str))
        
    def test_default(self):
        assert isinstance({'a':1,'b':'two', 'c':'three'}, Rec(a=int, __=str))
        assert not isinstance({'a':1,'b':'two', 'c':3}, Rec(a=int, __=str))
        assert not isinstance({'a':1,'b':'two', 'c':'three'}, Rec(a=int))
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Rec(a=int, b=str))
        Rec(a=int, b=str).register_instance(baz)
        assert isinstance(baz, Rec(a=int, b=str))
        
    def test_structural(self):
        assert isinstance({'a': 1}, Rec(a=int))
        assert not isinstance(1, Rec(a=int))
        assert not isinstance({'a': 1, 'b': 2}, Rec(a=int))
        assert not isinstance({'a': 'one'}, Rec(a=int))
        assert isinstance({'a': 1, 'b': 'two'}, Rec(a=int,b=str))
        try:
            assert isinstance({'a': 1, 'b': 'two'}, {'a':int,'b':str})
            assert False, 'Expected error'
        except TypeError as e:
            assert 'must be a type' in str(e), e
        assert isinstance({'a': 1, 'b': 'two'}, Rec(a=int,__b=str))
        assert isinstance({'a': 1}, Rec(a=int,__b=str))
        assert isinstance([1, 'two'], Rec(int,str))
        assert not isinstance([1, 2], Rec(int,str))
        
    def test_is_subclass(self):
        assert issubclass(dict, Mapping)
        assert issubclass(dict, Rec())
        assert not issubclass(tuple, Mapping)
        assert issubclass(tuple, Rec())
        assert not issubclass(list, Mapping)
        assert not issubclass(list, Rec())
        
        
class AltTest(TestCase):
    
    def test_alt_subclass(self):
        class Bar(Alt(int, str)): pass
        bar = Bar()
        assert isinstance(bar, Alt(int, str))
        assert not isinstance(bar, Alt(int, int))
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Alt(int, str))
        Alt(int, str).register_instance(baz)
        assert isinstance(baz, Alt(int, str))

    def test_structural(self):
        assert isinstance('one', Alt(int, str))
        assert isinstance(1, Alt(int, str))
        assert not isinstance(1.0, Alt(int, str))
        
        assert not issubclass(float, Alt(int, str))
        assert issubclass(int, Alt(int, str))
        assert issubclass(str, Alt(int, str))
        
        assert not issubclass(type, Alt)
        assert not issubclass(int, Alt)
        assert issubclass(Alt, Alt)
        assert issubclass(Opt, Alt)
        

class OptTest(TestCase):
    
    def test_subclass(self):
        class Bar(Opt(int)): pass
        bar = Bar()
        assert isinstance(bar, Opt(int))
        assert not isinstance(bar, Opt(str))
        assert isinstance(bar, Alt(none=None, value=int))
        assert not isinstance(bar, Alt(none=None, value=str))
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Opt(int))
        Opt(int).register_instance(baz)
        assert isinstance(baz, Opt(int))
        
    def test_normalize(self):
        foo = Opt([int])
        assert foo == Alt(none=None, value=Seq(int)), repr(foo)
        
    def test_structural(self):
        assert isinstance(None, Opt(int))
        assert isinstance(1, Opt(int))
        assert not isinstance('one', Opt(int))
        
        
class ClsTest(TestCase):
    
    def test_class_register(self):
        class Bar: pass
        class Baz: pass
        bar = Bar()
        assert not isinstance(bar, Cls(Baz))
        Cls(Baz).register_instance(bar)
        assert isinstance(bar, Cls(Baz))
        
        assert issubclass(Bar, Cls(Bar))
        assert not issubclass(Baz, Cls(Bar))
        Cls(Bar).register(Baz)
        assert issubclass(Baz, Cls(Bar))

    def test_structural(self):
        class Bar: pass
        bar = Bar()
        assert isinstance(bar, Cls(Bar))
        
    def test_inheritance(self):
        assert issubclass(Cls(int), Cls)
        assert issubclass(int, Cls(int))
        assert not issubclass(int, Cls)
        
    def test_attributes(self):
        class Foo: pass
        assert Cls(Foo, x=int) == And(Cls(Foo), Atr(x=int)), Cls(Foo, x=int)
        r = repr(Cls(Foo, x=int))
        assert r == "And(Atr(x=int),Cls(Foo))", r
        
        
class AndTest(TestCase):
    
    def test_and_register(self):
        class Bar: pass
        class Baz: pass
        bar = Bar()
        baz = Baz()
        assert not isinstance(bar, And(Bar, Atr(a=int)))
        assert not isinstance(baz, And(Baz, Atr(a=int)))
        And(Bar, Atr(a=int)).register_instance(bar)
        assert isinstance(bar, And(Bar, Atr(a=int)))
        assert not isinstance(baz, And(Bar, Atr(a=int)))
        assert not isinstance(baz, And(Baz, Atr(a=int)))
        And(Baz, Atr(a=int)).register_instance(baz)
        assert isinstance(bar, And(Bar, Atr(a=int)))
        assert not isinstance(baz, And(Bar, Atr(a=int)))
        assert isinstance(baz, And(Baz, Atr(a=int)))
        
    def test_structural(self):
        class Foo:
            def __init__(self, x):
                self.x = x
        ifoo = Foo(1)
        sfoo = Foo('one')
        assert isinstance(ifoo, Foo)
        assert isinstance(sfoo, Cls(Foo))
        assert isinstance(ifoo, And(Foo, Atr(x=int)))
        assert not isinstance(sfoo, And(Foo, Atr(x=int)))
        
        assert not issubclass(int, And(int, str))
        
        assert isinstance(ifoo, Cls(Foo, x=int))
        
        
class OrTest(TestCase):
    
    def test_or_structural(self):
        assert isinstance(1, Or(int, str))
        assert isinstance('one', Or(int, str))
        assert not isinstance(1.0, Or(int, str))
        
        assert not issubclass(float, Or(int, str))
        assert issubclass(int, Or(int, str))
        assert issubclass(str, Or(int, str))
        
        assert issubclass(int, Or(Atr(a=str), int))

        
class AnyTest(TestCase):
    
    def test_int(self):
        assert isinstance(1, ANY)
        

class OrderTest(TestCase):
    
    def test_order(self):
        ordered = And.transitive_ordered([int, And(str, float)])
        assert len(ordered) == 3, ordered
        
        
class SubTest(TestCase):
    
    def test_subinstance(self):
        assert isinstance(int, Sub(Cls(int)))
        assert isinstance(Alt(int, str), Sub(Sum))
        assert not isinstance(Alt(int, str), Sub(Product))


class BacktrackTest(TestCase):
    
    def test_verify(self):
        def simple_verify(value, spec):
            def check(vsn):
                (value, spec, _) = vsn
                try: return spec._backtrack(value, callback)
                except TypeError: raise
                except:
                    if isinstance(value, spec): return True
                    else: raise TypeError
            callback = lambda _, vsn: True and list(map(check, vsn))
            try: return check((value, TSMeta._normalize(spec), None))
            except: return False
        assert simple_verify(1, int)
        assert simple_verify([1,2,3], Seq())
        assert simple_verify(1, Opt(int))
        assert simple_verify([1,2,None,3], Seq(Opt(int)))
        assert not simple_verify([1,2,None,3.0], Seq(Opt(int)))
        assert simple_verify((1, 2), And(Seq(int), Rec(int, int)))
        assert not simple_verify((1, 2), And(Seq(int), Rec(int, str)))
    
        


