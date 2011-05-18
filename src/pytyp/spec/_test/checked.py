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

from pytyp.spec.check import checked
from pytyp.spec.abcs import Seq, Rec


@checked
def str_len(s:str) -> int:
    return len(s)

class Checked():
    
    @checked
    def str_len(self, s:str) -> int:
        return len(s)
    
    @checked
    def bad_len(self, s:str) -> int:
        return 'wrong'
    
    @checked
    def args(self, *args:Seq(int)):
        return args

    @checked
    def kargs(self, **kargs:Rec(a=int,__=str)):
        return kargs


class CheckedTest(TestCase):
    
    def test_function(self):
        assert str_len('abc') == 3
        try:
            str_len([1,2,3])
            assert False, 'Expected error'
        except TypeError:
            pass
    
    def test_method(self):
        c = Checked()
        assert c.str_len('abc') == 3
        try:
            c.str_len([1,2,3])
            assert False, 'Expected error'
        except TypeError:
            pass
        try:
            c.bad_len('abc')
            assert False, 'Expected error'
        except TypeError:
            pass

    def test_args(self):
        c = Checked()
        r = c.args(1,2)
        assert r == (1,2)
        try:
            c.args('poop')
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_kargs(self):
        c = Checked()
        r = c.kargs(a=1)
        assert r == {'a': 1}
        r = c.kargs(a=1,b='two',c='three')
        assert r == {'a': 1, 'b':'two', 'c':'three'}
        try:
            c.args('poop')
            assert False, 'Expected error'
        except TypeError:
            pass
