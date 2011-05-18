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

from pytyp.s11n.base import encode, decode
from pytyp._test.support import SimpleArgs, NamedArgs, ArgsAndKArgs,\
    MissingKArgs, TypedKArgs


class Example():
    
    def __init__(self, foo):
        self.foo = foo
        
    def __repr__(self):
        return '<Example({0})>'.format(self.foo)
    
    def __eq__(self, other):
        return self.foo == other.foo
    

class Container():

    def __init__(self, *examples:[Example]):
        self.examples = list(examples) # avoid issues with tuple/list
        
    def __repr__(self):
        return '<Container({0})>'.format(','.join(map(repr, self.examples)))
    
    def __eq__(self, other):
        return other.examples == self.examples


class RoundtripTest(TestCase):
    
    def assert_roundtrip(self, spec, obj, target=None):
        target = target or obj
        intermediate = encode(obj)
        result = decode(intermediate, spec)
        assert result == target, result
        
    def test_atomic(self):
        self.assert_roundtrip(int, 1)
    
    def test_tuple(self):
        self.assert_roundtrip((SimpleArgs, NamedArgs),
                              (SimpleArgs(1,2,3), NamedArgs(1,2)))

    def test_args_and_kargs(self):
        try:
            self.assert_roundtrip(ArgsAndKArgs,
                                  ArgsAndKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
                                               foo=7, bar=8))
            assert False, 'expected error'
        except TypeError as e:
            print(e)
            assert 'Cannot encode' in str(e)
            
    def test_args_as_list(self):
        self.assert_roundtrip(Container,
                              Container(Example('abc'), Example('xyz')))

    # uses *args in map
#    def test_missing_kargs(self):
#        try:
#            self.assert_roundtrip(MissingKArgs,
#                                  MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
#                                               foo=7, bar=NamedArgs(8,9)))
#            raise Exception('expected error')
#        except AttributeError:
#            pass
#        try:
#            self.assert_roundtrip(MissingKArgs,
#                                  MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
#                                               foo=7, bar=8),
#                                  strict=False)
#            raise Exception('expected error')
#        except AssertionError:
#            pass
#        # here we don't have an exact match because we used non-strict matching,
#        # which allowed for missing kargs
#        self.assert_roundtrip(MissingKArgs,
#                              MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
#                                           foo=7, bar=8),
#                              target=MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6)),
#                              strict=False)
        
    def test_typed_kargs(self):
        self.assert_roundtrip(TypedKArgs, TypedKArgs(foo=SimpleArgs(1,2,3)))


