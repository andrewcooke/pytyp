
from abc import ABCMeta
from collections import Sequence
from unittest import TestCase

from pytyp.spec.abcs import Seq, Map, Alt, Opt, Cls


class SeqAbcTest(TestCase):
    
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


class SeqRegisterTest(TestCase):
    
    def test_register(self):
        class Foo: pass
        foo = Foo()
        assert not isinstance(foo, Seq(int))
        Seq(int).register_instance(foo)
        assert isinstance(foo, Seq(int))
        
        
class MapTest(TestCase):
    
    def test_subclass(self):
        class Bar(dict, Map(a=int, b=str)): pass
        bar = Bar({'a':1, 'b':'two'})
        assert bar['a'] == 1
        assert isinstance(bar, Map(a=int, b=str))
        assert not isinstance(bar, Map(a=int, b=int))
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Map(a=int, b=int))
        Map(a=int, b=str).register_instance(baz)
        assert isinstance(baz, Map(a=int, b=int))
        
        
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


class OptTest(TestCase):
    
    def test_subclass(self):
        class Bar(Opt(int)): pass
        bar = Bar()
        assert isinstance(bar, Opt(int))
        assert not isinstance(bar, Opt(str))
        assert isinstance(bar, Alt(none=None, value=int))
        
    def test_register(self):
        class Baz(): pass
        baz = Baz()
        assert not isinstance(baz, Opt(int))
        Opt(int).register_instance(baz)
        assert isinstance(baz, Opt(int))
        
        
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
        print('---------')
        assert not isinstance(baz, Cls(Bar, int))
        assert isinstance(baz, Cls(Baz, int))
        


