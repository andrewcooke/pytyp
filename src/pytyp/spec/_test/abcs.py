
from abc import ABCMeta
from collections import Sequence
from unittest import TestCase

from pytyp.spec.abcs import Seq, Map, Alt, Opt, Cls, normalize, Any, Delayed,\
    fmt


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
        assert sint._abc_type_arguments == ((0, int),), sint._abc_type_arguments
        
    def test_mixin(self):
        SFloat = Seq(float)
        class Baz(SFloat):
            def __getitem__(self, index):
                return 42
            def __len__(self):
                return 42
        baz = Baz()
        assert isinstance(baz, Sequence)
        assert isinstance(baz, SFloat)

    def test_list(self):
        class Bar(list, Seq(int)): pass
        bar = Bar([1,2,3])
        assert isinstance(bar, Seq(int))
        assert isinstance(bar, Sequence)
        assert isinstance(bar, list)
        assert bar[1:] == [2,3], bar[1:]
        assert not isinstance(bar, Seq(float))

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
        assert isinstance(boo, Sequence)
        assert not isinstance(boo, Seq(int))
        
    def test_is_subclass(self):
        assert issubclass(list, Sequence)
        assert issubclass(list, Seq)
        assert not issubclass(list, Seq(int))

    def test_register(self):
        class Foo: pass
        foo = Foo()
        assert not isinstance(foo, Seq(int))
        Seq(int).register_instance(foo)
        assert isinstance(foo, Seq(int))
        
    def test_structural(self):
        assert isinstance([1,2,3], Seq(int))
        assert not isinstance(1, Seq(int))
        assert not isinstance([1,'two'], Seq(int))
        assert isinstance([1, None], Seq(Opt(int)))
        assert isinstance([1, None, 'three'], Seq(Any))
        
    def test_loop(self):
        d = Delayed()
        d2 = Alt(int, d, str)
        d.set(d2)
        assert fmt(d) == 'Delayed(Alt(0=int,1=...,2=str))', fmt(d)
        assert isinstance(1, d)
        assert isinstance('two', d)
        
        
class MapTest(TestCase):
    
    def test_subclass(self):
        class Bar(dict, Map(a=int, b=str)): pass
        bar = Bar({'a':1, 'b':'two'})
        assert bar['a'] == 1
        assert isinstance(bar, Map(a=int, b=str))
        assert not isinstance(bar, Map(a=int, b=int))
        assert isinstance({}, Map)
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Map(a=int, b=str))
        Map(a=int, b=str).register_instance(baz)
        assert isinstance(baz, Map(a=int, b=str))
        
    def test_structural(self):
        assert isinstance({'a': 1}, Map(a=int))
        assert not isinstance(1, Map(a=int))
        assert not isinstance({'a': 1, 'b': 2}, Map(a=int))
        assert not isinstance({'a': 'one'}, Map(a=int))
        assert isinstance({'a': 1, 'b': 'two'}, Map(a=int,b=str))
        try:
            assert isinstance({'a': 1, 'b': 'two'}, {'a':int,'b':str})
            assert False, 'Expected error'
        except TypeError as e:
            assert 'must be a type' in str(e), e
        assert isinstance({'a': 1, 'b': 'two'}, Map(a=int,__b=str))
        assert isinstance({'a': 1}, Map(a=int,__b=str))
        assert isinstance([1, 'two'], Map(int,str))
        assert not isinstance([1, 2], Map(int,str))
        
        
class AltTest(TestCase):
    
    def test_subclass(self):
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
        foo = normalize(Opt([int]))
        assert foo == Alt(none=None, value=Seq(int))
        
    def test_structural(self):
        assert isinstance(None, Opt(int))
        assert isinstance(1, Opt(int))
        assert not isinstance('one', Opt(int))
        
        
class ClsTest(TestCase):
    
    def test_class_register(self):
        class Bar: pass
        bar = Bar()
        class Baz: pass
        baz = Baz()
        assert not isinstance(bar, Cls(Bar, int))
        assert not isinstance(baz, Cls(Baz, int))
        Cls(Bar, int).register_instance(bar)
        assert isinstance(bar, Cls(Bar, int))
        assert not isinstance(baz, Cls(Bar, int))
        assert not isinstance(baz, Cls(Baz, int))
        Cls(Baz, int).register_instance(baz)
        assert isinstance(bar, Cls(Bar, int))
        assert not isinstance(baz, Cls(Bar, int))
        assert isinstance(baz, Cls(Baz, int))
    
    def test_structural(self):
        class Foo:
            def __init__(self, x):
                self.x = x
        ifoo = Foo(1)
        sfoo = Foo('one')
        assert isinstance(ifoo, Cls(Foo))
        assert isinstance(sfoo, Cls(Foo))
        assert isinstance(ifoo, Cls(Foo, x=int))
        assert not isinstance(sfoo, Cls(Foo, x=int))
