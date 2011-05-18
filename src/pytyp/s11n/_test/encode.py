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

from pytyp._test.support import SimpleArgs
from pytyp.s11n.base import Encoder, EncodeError


class Example():
    
    def __init__(self, foo):
        self.foo = foo
        
    def __repr__(self):
        return '<Example({0})>'.format(self.foo)
    

class Container():

    def __init__(self, *examples:[Example]):
        self.examples = examples
        
    def __repr__(self):
        return '<Container({0})>'.format(','.join(map(repr, self.examples)))


class EncodeTest(TestCase):
    
    def assert_encode(self, value, target=None, encode=Encoder()):
        if target is None: target = value
        result = encode(value)
        assert result == target, result
        
    def test_list(self):
        self.assert_encode([])
        self.assert_encode([1,2,3])
        self.assert_encode((1,2,3), [1,2,3])
    
    def test_map(self):
        self.assert_encode({})
        self.assert_encode({'a':1, 'b':2})
        
    def test_atomic(self):
        self.assert_encode('foo')
        self.assert_encode(1)
        self.assert_encode(object())
        
    def test_object(self):
        self.assert_encode(Example('xyz'), {'foo': 'xyz'})
        self.assert_encode(Container(Example('xyz'), Example('abc')), [{'foo': 'xyz'}, {'foo': 'abc'}])
    
    def test_circular(self):
        encode = Encoder()
        s = SimpleArgs(1,2,3)
        s.a = s
        try:
            encode(s)
            assert False, 'Expected error'
        except EncodeError as e:
            assert 'Circular' in str(e), e
        