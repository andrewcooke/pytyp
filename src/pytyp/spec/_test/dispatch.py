
from unittest import TestCase

from pytyp.spec.abcs import Delayed, Alt, Seq, ANY, Sub, Sum
from pytyp.spec.dispatch import overload


class ExpandTest(TestCase):
    
    def test_sexpr(self):
        sexpr = Delayed()
        sexpr.set(Alt(Seq(sexpr), ANY))
        
        class Count:
            
            @overload
            def __call__(self, spec, vsn):
                return sum(map(self.count, vsn))
        
            @__call__.intercept
            def sum(self, spec:Sub(Sum), vsn):
                for entry in vsn:
                    try:
                        return self.count(entry)
                    except TypeError:
                        pass
                    
            def count(self, vsn):
                (value, spec, _) = vsn
                try:
                    return spec._for_each(value, self)
                except AttributeError:
                    return 1
                
        n = sexpr._for_each([1,2,[3,[4,5],6,[7]]], Count())
        assert n == 7, n
        
        
