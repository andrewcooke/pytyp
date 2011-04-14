
from unittest import TestCase

from pytyp.spec.base import Delayed, Alt
from pytyp.spec.future import TypedProperty, Typed
from pytyp.spec.check import checked


#def tree_functor_1(leaf_type):
#        
#    tree_type = Delayed()
#
#    class Node(Typed):
#        
#        value = TypedProperty(leaf_type)
#        left = TypedProperty(None, tree_type)
#        right = TypedProperty(None, tree_type)
#        
#        @checked
#        def __init__(self, value:leaf_type):
#            super(Node, self).__init__()
#            self.value = value
#        
#        @checked
#        def add(self, value:leaf_type):
#            if value < self.value:
#                side = self.p.left
#            else:
#                side = self.p.right
#            side.set_on(none=lambda _: value,
#                        leaf=lambda l: Node(l).add(value),
#                        node=lambda n: n.add(value))
#            return self
#        
#        def __len__(self):
#            return 1 + self.p.left.on(none=lambda _: 0,
#                                      leaf=lambda l: 1,
#                                      node=lambda n: len(n)) \
#                    + self.p.right.on(none=lambda _: 0,
#                                      leaf=lambda l: 1,
#                                      node=lambda n: len(n))
#            
#            
#    class Tree(Typed):
#        
#        root = TypedProperty(None, tree_type)
#        
#        def add(self, value:leaf_type):
#            self.p.root.set_on(none=lambda _: value,
#                               leaf=lambda l: Node(l).add(value),
#                               node=lambda n: n.add(value))
#            
#        def __len__(self):
#            return self.p.root.on(none=lambda _: 0,
#                                  leaf=lambda l: 1,
#                                  node=lambda n: len(n))
#            
#            
#    tree_type += Alt(none=None, leaf=leaf_type, node=Node)
#        
#    return Tree


def tree_functor_2(leaf_type):
    
        
    tree_type = Delayed()
    

    class TreeProperty(TypedProperty):
        
        def __init__(self, value):
            super(TreeProperty, self).__init__(value, tree_type)
        
        @staticmethod
        def size(value, spec):
            return spec.on(value,
                           none=lambda _: 0,
                           leaf=lambda l: 1,
                           node=lambda n: len(n))
            
        @staticmethod
        def set_add(value, spec, leaf:leaf_type):
            return spec.on(value,
                           none=lambda _: leaf,
                           leaf=lambda l: Node(l).add(leaf),
                           node=lambda n: n.add(leaf))


    class Node(Typed):
        
        value = TypedProperty(leaf_type)
        left = TreeProperty(None)
        right = TreeProperty(None)
        
        @checked
        def __init__(self, value:leaf_type):
            super(Node, self).__init__()
            self.value = value
        
        @checked
        def add(self, value:leaf_type):
            if value < self.value:
                self.p.left.set_add(value)
            else:
                self.p.right.set_add(value)
            return self
        
        def __len__(self):
            return 1 + self.p.left.size() + self.p.right.size()
            
            
    class Tree(Typed):
        
        root = TreeProperty(None)
        
        def add(self, value:leaf_type):
            self.p.root.set_add(value)
            
        def __len__(self):
            return self.p.root.size()

            
    tree_type += Alt(none=None, leaf=leaf_type, node=Node)
       
    return Tree


class TreeFunctorTest(TestCase):
    
    def assert_functor(self, functor):
        Tree = functor(int)
        t1 = Tree()
        t1.value = 'poot'
        t1.add(1)
        try:
            t1.add('bad')
            assert False, 'Expected error'
        except TypeError:
            pass
        for n in [8,3,6,5,9,2]:
            t1.add(n)
        assert len(t1) == 7, len(t1)   

    def test_functor_1(self):
#        self.assert_functor(tree_functor_1)
        self.assert_functor(tree_functor_2)
        
        
class TypedTest(TestCase):
    
    def test_doc_bug(self):
        
        class C(Typed):
            
            a = TypedProperty(int)
            b = TypedProperty('foo', str)
            
            def __init__(self):
                super(C, self).__init__()
                self.a = 1
                
        c = C()
        assert c.a == 1
        try:
            c.a = 'foo'
            assert False, 'Expected error'
        except TypeError:
            pass
        assert c.b == 'foo', c.b
        c.a = 2
        assert c.a == 2
        try:
            c.b = 2
            assert False, 'Expected error'
        except TypeError:
            pass
