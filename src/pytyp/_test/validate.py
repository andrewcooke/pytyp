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
from pytyp import validate, Opt
from pytyp._test.support import SimpleArgs
from collections import namedtuple


class ValidateTest(TestCase):
    
    def test_direct(self):
        validate(str, 'a')
        validate(int, 1)
        validate(list, [1,2])
        validate(dict, {1:2})
        validate(object, object())
        validate(SimpleArgs, SimpleArgs(1,2,3))
        
    def assert_error(self, trigger):
        try:
            trigger()
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_direct_fail(self):
        self.assert_error(lambda: validate(str, 1))
        self.assert_error(lambda:validate(int, [1,2]))
        self.assert_error(lambda:validate(list, {1:2}))
        self.assert_error(lambda:validate(dict, object()))
        validate(object, SimpleArgs(1,2,3)) # inclusional
        self.assert_error(lambda:validate(SimpleArgs, 'a'))
    
    def test_polymorphic_none(self):
        validate(None, 'a')
        validate(None, 1)
        validate(None, [1,2])
        validate(None, {1:2})
        validate(None, object())
        validate(None, SimpleArgs(1,2,3))
    
    def test_maybe(self):
        validate(Opt(str), None)
        validate(Opt(int), None)
        validate(Opt(list), None)
        validate(Opt(dict), None)
        validate(Opt(object), None)
        validate(Opt(SimpleArgs), None)
    
    def test_polymorphic_list(self):
        validate([int], [1,2,3])
        validate([int], [])
        validate([Opt(int)], [1,None,3])
        validate(None, [1,2,3])
        validate([None], [1,2,3])
        self.assert_error(lambda: validate([int], [1,'two',3]))
        self.assert_error(lambda: validate([], [1,2,3]))
        self.assert_error(lambda: validate([int,str], [1,'two']))
        
    def test_product_as_tuple(self):
        validate((int,), [1])
    
    def test_product_tuple(self):
        validate((int, str), (1, 'a'))
        self.assert_error(lambda: validate((int, str), ('a', 1)))
        NT = namedtuple('NT', 'a, b')
        validate(NT(int, str), NT(1, 'a'))
        self.assert_error(lambda: validate(NT(int, str), NT('a', 1)))
        validate(NT(int, str), NT(a=1, b='a'))
        validate(NT(a=int, b=str), NT(b='a', a=1))
        self.assert_error(lambda: validate(NT(int, str), NT(a='a', b=1)))
        