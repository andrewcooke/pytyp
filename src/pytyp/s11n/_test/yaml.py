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

from pytyp._test.support import SimpleArgs, NamedArgs, MixedArgs, TypedArgs, \
    Config, User, Permission

try:
    from pytyp.yaml import dump, make_load
    
    
    class DumpTest(TestCase):
        
        def assert_dump(self, value, target):
            result = dump(value)
            assert result == target, repr(result)  
        
        def test_native(self):
            self.assert_dump('abc', 'abc\n...\n')
            self.assert_dump([1,2.3], '[1, 2.3]\n')
            
        def test_classes(self):
            self.assert_dump(SimpleArgs(1, 2, 3), '{a: 1, b: 2, c: 3}\n')
            self.assert_dump(NamedArgs(1, 2), '{p: 1, q: 2}\n')
            self.assert_dump(MixedArgs(1, 2), '{x: 1, y: 2}\n')
            
        def test_nested(self):
            self.assert_dump(TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)), 
                             'x: {p: 1, q: 2}\ny: {a: 1, b: 2, c: 3}\n')
    
    class LoadTest(TestCase):
        
        def assert_load(self, type_, value, target):
            load = make_load(type_)
            result = load(value)
            assert result == target, result 
        
        def test_native(self):
            self.assert_load(str, 'abc\n...\n', 'abc')
            self.assert_load(list, '[1, 2.3]\n', [1,2.3])
            
        def test_classes(self):
            self.assert_load(SimpleArgs, '{a: 1, b: 2, c: 3}\n', SimpleArgs(1, 2, 3))
            self.assert_load(NamedArgs, '{p: 1, q: 2}\n', NamedArgs(1, 2))
            self.assert_load(MixedArgs, '{x: 1, y: 2}\n', MixedArgs(1, 2))
            
        def test_nested(self):
            self.assert_load(TypedArgs, 
                               'x: {p: 1, q: 2}\ny: {a: 1, b: 2, c: 3}\n', 
                               TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)))
    
    
    class ConfigTest(TestCase):
        
        def test_config(self):
            load = make_load(Config)
            config = load('''
    users:
    - name: bob
      email: bob@example.com
    - name: andrew
      email: andrew@acooke.org
    permission: 
      resource: foo.txt
      rw: r
    ''')
            assert isinstance(config, Config), config
            assert len(config.users) == 2, config.users
            for user in config.users:
                assert isinstance(user, User), user
            assert isinstance(config.permission, Permission), config.permission

except ImportError:
    pass
