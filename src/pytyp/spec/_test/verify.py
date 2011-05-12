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
from collections import namedtuple

from pytyp.spec.abcs import Opt, Alt, ANY, Rec
from pytyp.spec.check import verify
from pytyp._test.support import SimpleArgs


class verifyTest(TestCase):
    
    def test_direct(self):
        verify('a', str)
        verify(1, int)
        verify([1,2], list)
        verify({1:2}, dict)
        verify(object(), object)
        verify(SimpleArgs(1,2,3), SimpleArgs)
        
    def assert_error(self, trigger):
        try:
            trigger()
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_direct_fail(self):
        self.assert_error(lambda: verify(1, str))
        self.assert_error(lambda:verify([1,2], int))
        self.assert_error(lambda:verify({1:2}, list))
        self.assert_error(lambda:verify(object(), dict))
        verify(SimpleArgs(1,2,3), object) # inclusional
        self.assert_error(lambda:verify(SimpleArgs, 'a'))
    
    def test_polymorphic(self):
        verify('a', ANY)
        verify(1, ANY)
        verify([1,2], ANY)
        verify({1:2}, ANY)
        verify(object(), ANY)
        verify(SimpleArgs(1,2,3), ANY)
    
    def test_maybe(self):
        verify(None, Opt(str))
        verify(None, Opt(int))
        verify(None, Opt(list))
        verify(None, Opt(dict))
        verify(None, Opt(object))
        verify(None, Opt(SimpleArgs))
        
    def test_alternatives(self):
        verify(1, Alt(int, str))
    
    def test_polymorphic_list(self):
        verify([1,2,3], [int])
        verify([], [int])
        verify([1,None,3], [Opt(int)])
        verify([1,2,3], ANY)
        verify([1,2,3], [ANY])
        self.assert_error(lambda: verify([1,'two',3], [int]))
        verify([1,2,3], [])
        verify([1,'two'], [int,str])
        
    def test_sequence_as_tuple(self):
        verify([1], (int,))
    
    def test_tuple_as_sequence(self):
        verify((1,2,3), [int])
    
    def test_product_tuple(self):
        verify((1, 'a'), (int, str))
        self.assert_error(lambda: verify(('a', 1), (int, str)))
        NT = namedtuple('NT', 'a, b')
        verify(NT(1, 'a'), NT(int, str))
        self.assert_error(lambda: verify(NT('a', 1), NT(int, str)))
        verify(NT(a=1, b='a'), NT(int, str))
        verify(NT(b='a', a=1), NT(a=int, b=str))
        self.assert_error(lambda: verify(NT(a='a', b=1), NT(int, str)))
        
    def test_product(self):
        verify({'a': 1, 'b': 'two'}, {'a': int, 'b': str})
        verify({'a': 1, 'b': 'two'}, Rec(a=int, b=str))
        verify((1, 'two'), {0: int, 1: str})
        verify((1, 'two'), Rec(int, str))
        verify([1, 'two'], {0: int, 1: str})
        verify([1, 'two'], Rec(int, str))

        