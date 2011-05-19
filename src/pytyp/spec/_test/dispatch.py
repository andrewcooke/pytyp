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
        
        
class PreviousTest(TestCase):
    
    def test_previous(self):
        
        class Previous:
            
            @overload
            def __call__(self, data, ignored):
                data.append(0)
                return data
            
            @__call__.intercept
            def one(self, data, previous:bool):
                data.append(1)
                if previous:
                    return self.one.previous(data, previous)
                else:
                    return data
        
        p = Previous()
        assert p([2], None) == [2,0], p([2])
        assert p([2], False) == [2,1], p([2], False)
        assert p([2], True) == [2,1,0], p([2], True)
        