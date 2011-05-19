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

from pytyp.spec.record import record, parse_args
from pytyp.spec.abcs import Seq
import pytyp.spec.abcs as abcs


def foo(a:int=6): return a
#def foo(a=6:int): return a


class ParseArgsTest(TestCase):
    
    def assert_parse(self, input, target):
        result = str(parse_args(input, abcs.__dict__))
        assert result == target, result
    
    def test_parse(self):
        self.assert_parse('a:int=1', "OrderedDict([('a', (int, '1'))])")
        self.assert_parse('a:int=1,b', "OrderedDict([('a', (int, '1')), ('b', (Cls(object), None))])")
        self.assert_parse('a:int=1,:int', "OrderedDict([('a', (int, '1')), (0, (int, None))])")
        self.assert_parse('a:int=1,b:int', "OrderedDict([('a', (int, '1')), ('b', (int, None))])")
        self.assert_parse('a:int=1,=2', "OrderedDict([('a', (int, '1')), (0, (Cls(object), '2'))])")
        self.assert_parse('a:int=1,b=2', "OrderedDict([('a', (int, '1')), ('b', (Cls(object), '2'))])")
        self.assert_parse('a:int=1,:int=2', "OrderedDict([('a', (int, '1')), (0, (int, '2'))])")
        self.assert_parse('a:int=1,,', "OrderedDict([('a', (int, '1')), (0, (Cls(object), None)), (1, (Cls(object), None))])")
        self.assert_parse('a:int,b:Rec(Seq(Opt(int)))', "OrderedDict([('a', (int, None)), ('b', (Rec(Seq(Opt(int))), None))])")
        self.assert_parse('a:str,__:int', "OrderedDict([('a', (str, None)), ('__', (int, None))])")
                          
                          
class RecordTest(TestCase):
    
    def test_syntax(self):
        record('Name', 'a:int,b:int=6', mutable=False)
        record('Name', ':,,:int=6,d:str="foo"')
    
    def test_default(self):
        Record = record('Record', 'a:int,b:int=6')
        r = Record(1,2)
        assert r.a == 1, r.a
        assert r['a'] == 1, r['a']
        assert r.b == 2, r.b
        assert r['b'] == 2, r['b']
        try:
            r.a = 3
            assert False, 'Expected immutable'
        except AttributeError:
            pass
        r2 = r._replace(b=3)
        assert r2.b == 3, r2.b
    
    def test_mutable(self):
        Record = record('Record', 'a:int,b:int=6', mutable=True, checked=False)
        r = Record(1,2)
        assert r.a == 1, r['a']
        assert r.b == 2, r.b
        r['a'] = 3
        r2 = r._replace(b=3)
        assert r2.a == 3, r2.a
        assert r2['a'] == 3, r2['a']
        assert r2.b == 3, r2.b
        try:
            r.c = 4
            assert False, 'Expected error'
        except TypeError:
            pass
        r.a = 'one'
        assert r.a == 'one', r.a

    def test_checked(self):
        Record = record('Record', 'a:int,b:int=6', mutable=True)
        r = Record(1,2)
        assert r.a == 1, r['a']
        assert r.b == 2, r.b
        r['a'] = 3
        r2 = r._replace(b=3)
        assert r2.a == 3, r2.a
        assert r2['a'] == 3, r2['a']
        assert r2.b == 3, r2.b
        try:
            r.a = 'one'
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_complex(self):
        record('Record', 'a:int,b:Rec(Seq(Opt(int)))')
        Record = record('Record', 'a:[int]')
        spec = Record._Record__specs['a']
        assert spec == Seq(int), spec
    
    def test_sizeable(self):
        Record = record('Record', 'a:str,__:int', mutable=True, verbose=True)
        r = Record(a='poop',foo=1)
        assert r.a == 'poop', r.a
        assert r['a'] == 'poop', r['a']
        assert r.foo == 1, r.foo
        assert r['foo'] == 1, r['foo']
        
        try:
            Record(a='poop',foo='one')
            assert False, 'Expected error'
        except TypeError:
            pass

    def test_str_tuple(self):
        StrTuple = record('StrTuple', ':str,:str')
        stuple = StrTuple('foo', 'bar')
        