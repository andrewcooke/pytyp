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

from pytyp.s11n.json import make_JSONDecoder, JSONEncoder
from pytyp._test.support import SimpleArgs, NamedArgs, MixedArgs, TypedArgs, \
    Config, User, Permission
from pytyp.spec.abcs import Alt
from pytyp.spec.record import record


class JSONDecoderTest(TestCase):
    
    def assert_decode(self, type_, value, target):
        JSONDecoder = make_JSONDecoder(type_)
        result = JSONDecoder().decode(value)
        assert result == target, result 
        return result
    
    def test_native(self):
        self.assert_decode(str, '"abc"', 'abc')
        self.assert_decode(list, '[1, 2.3]', [1,2.3])
        
    def test_classes(self):
        self.assert_decode(SimpleArgs, '{"a": 1, "c": 3, "b": 2}', SimpleArgs(1, 2, 3))
        self.assert_decode(NamedArgs, '{"q": 2, "p": 1}', NamedArgs(1, 2))
        self.assert_decode(MixedArgs, '{"y": 2, "x": 1}', MixedArgs(1, 2))
        
    def test_alt(self):
        self.assert_decode(Alt(NamedArgs, MixedArgs), '{"q": 2, "p": 1}', NamedArgs(1, 2))
        self.assert_decode(Alt(NamedArgs, MixedArgs), '{"y": 2, "x": 1}', MixedArgs(1, 2))
        
    def test_nested(self):
        self.assert_decode(TypedArgs, 
                           '{"y": {"a": 1, "c": 3, "b": 2}, "x": {"q": 2, "p": 1}}', 
                           TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)))
        
    def test_record(self):
        R = record('R', '__:ANY')
        r = self.assert_decode(R, '{"a": 1, "c": 3, "b": 2}', R(a=1,b=2,c=3)) 
        assert r.a == 1
        

class ConfigTest(TestCase):
    
    def test_config(self):
        JSONDecoder = make_JSONDecoder(Config)
        config = JSONDecoder().decode('''
{"users": [
 {"name": "bob",
  "email": "bob@example.com"},
 {"name": "andrew",
  "email": "andrew@acooke.org"}],
 "permission": 
  {"resource": "foo.txt",
   "rw": "r"}
}''')
        assert isinstance(config, Config), config
        assert len(config.users) == 2, config.users
        for user in config.users:
            assert isinstance(user, User), user
        assert isinstance(config.permission, Permission), config.permission
        
        
class JSONEncoderTest(TestCase):
    
    def setUp(self):
        self.__encoder = JSONEncoder()
    
    def assert_encode(self, value, target):
        result = self.__encoder.encode(value)
        if result != target:
            target = target.translate({'"':"'", "'":'"'})
        assert result == target, (result, target, type(result))  
    
    def test_encode_native(self):
        self.assert_encode('abc', '"abc"')
        self.assert_encode([1,2.3], '[1, 2.3]')
        
    def test_classes(self):
        self.assert_encode(SimpleArgs(1, 2, 3), '{"a": 1, "c": 3, "b": 2}')
        self.assert_encode(NamedArgs(1, 2), '{"q": 2, "p": 1}')
        self.assert_encode(MixedArgs(1, 2), '{"y": 2, "x": 1}')
        
    def test_nested(self):
        self.assert_encode(TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)), 
                           '{"y": {"a": 1, "c": 3, "b": 2}, "x": {"q": 2, "p": 1}}')
