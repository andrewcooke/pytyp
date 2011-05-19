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
from pytyp.s11n.base import decode, cls_to_rec, cls_to_seq
from pytyp.spec.abcs import Seq, Opt, Rec, Alt, Cls, ANY


class Simple:
    
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
    def __eq__(self, other):
        return other.a == self.a and other.b == self.b


class SimpleXY:
    
    def __init__(self, x, y=None):
        self.x = x
        self.y = y
        
    def __eq__(self, other):
        return other.x == self.x and other.y == self.y


class SimpleTyped:
    
    def __init__(self, a:int, b:str):
        self.a = a
        self.b = b
        
    def __eq__(self, other):
        return other.a == self.a and other.b == self.b


class SimpleKArgs:
    
    def __init__(self, a, **kargs):
        self.a = a
        self.kargs = kargs
        
    def __eq__(self, other):
        return other.a == self.a and other.kargs == self.kargs


class SimpleTypedKArgs:
    
    def __init__(self, a, **kargs:Rec(__=int)):
        self.a = a
        self.kargs = kargs
        
    def __eq__(self, other):
        return other.a == self.a and other.kargs == self.kargs


class SimpleArgs:
    
    def __init__(self, a, *args):
        self.a = a
        self.args = args
        
    def __eq__(self, other):
        return other.a == self.a and other.args == self.args


class SimpleNested:
    
    def __init__(self, a:SimpleArgs, b:SimpleKArgs):
        self.a = a
        self.b = b
        
    def __eq__(self, other):
        return other.a == self.a and other.b == self.b


class RewriteTest(TestCase):
    
    def assert_decode(self, data, spec, target=None):
        if target is None: target = data
        result = decode(data, spec)
        try:
            assert result == target, result
        except Exception as e:
            wrapper = Exception(str(result))
            wrapper.cause = e
            raise wrapper
        
    def test_list(self):
        self.assert_decode([], Seq())
        self.assert_decode([1,2], Seq())
        self.assert_decode([1,2], Seq(int))
        self.assert_decode([1,None,3], Seq(Opt(int)))
        self.assert_decode((1,2), Seq(int), [1,2])
    
    def test_dict(self):
        self.assert_decode({}, Rec())
        self.assert_decode({'a':int,'b':str}, Rec(__=Alt(int, str)))
    
    def test_class_from_dict(self):
        self.assert_decode({'a': 1, 'b': 2}, Cls(Simple), Simple(1, 2))
        self.assert_decode({'a': 1, 'b': 'two'}, Cls(SimpleTyped), SimpleTyped(1, 'two'))
        self.assert_decode({'a': 1, 'x': 2, 'y': 'three'}, Cls(SimpleKArgs), SimpleKArgs(1, x=2, y='three'))

    def test_class_from_list(self):
        self.assert_decode([1, 2], Cls(Simple), Simple(1, 2))
        self.assert_decode([1, 'two'], Cls(SimpleTyped), SimpleTyped(1, 'two'))
        self.assert_decode([1, 2, 'three'], Cls(SimpleArgs), SimpleArgs(1, 2, 'three'))

    def test_nested(self):
        self.assert_decode([['one', 'two'], {'a':1, 'b':2}], Cls(SimpleNested), SimpleNested(SimpleArgs('one', 'two'), SimpleKArgs(a=1, b=2)))
        
    def test_opt(self):
        self.assert_decode([[1,2]], Seq(Simple), [Simple(1,2)])
        self.assert_decode([None], Seq(Opt(Simple)), [None])
        self.assert_decode([[1,2]], Seq(Opt(Simple)), [Simple(1,2)])
        self.assert_decode([[1,2], None], Seq(Opt(Simple)), [Simple(1,2), None])

    def test_alt(self):
        self.assert_decode({'a':1, 'b':2}, Simple, Simple(1,2))
        self.assert_decode({'x':1, 'y':2}, SimpleXY, SimpleXY(1,2))
        try:
            self.assert_decode({'x':1, 'y':2}, Simple, Simple(1, 2))
            assert False, 'Expected error'
        except TypeError:
            pass
        self.assert_decode({'a':1, 'b':2}, Alt(Simple, SimpleXY), Simple(1,2))
        self.assert_decode({'a':1, 'b':2}, Alt(SimpleXY, Simple), Simple(1,2))


class ClsToRecTest(TestCase):
    
    def assert_convert(self, cls, target, convert=cls_to_rec):
        rec = convert(cls)
        assert rec == target, rec
        
    def test_simple(self):
        self.assert_convert(Cls(Simple), Rec(a=ANY,b=ANY))
        self.assert_convert(Cls(SimpleTyped), Rec(a=int,b=str))
        self.assert_convert(Cls(SimpleKArgs), Rec(a=ANY,__=ANY))
        self.assert_convert(Cls(SimpleTypedKArgs), Rec(a=ANY,__=int))
        try:
            self.assert_convert(Cls(SimpleArgs), Rec())
            assert False, 'Expected error'
        except TypeError:
            pass
        self.assert_convert(Cls(SimpleXY), Rec(x=ANY,__y=ANY))
        self.assert_convert(Cls(Simple), Rec(ANY,ANY), cls_to_seq)
        self.assert_convert(Cls(SimpleTyped), Rec(int,str), cls_to_seq)
        self.assert_convert(Cls(SimpleArgs), Rec(ANY,__=ANY), cls_to_seq)
