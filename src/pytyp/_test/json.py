
from unittest import TestCase

from pytyp.json import make_JSONDecoder, JSONEncoder
from pytyp._test.support import SimpleArgs, NamedArgs, MixedArgs, TypedArgs, \
    Config, User, Permission
from collections import namedtuple
from pytyp import Choice


class JSONDecoderTest(TestCase):
    
    def assert_decode(self, type_, value, target):
        JSONDecoder = make_JSONDecoder(type_)
        result = JSONDecoder().decode(value)
        assert result == target, result 
    
    def test_native(self):
        self.assert_decode(str, '"abc"', 'abc')
        self.assert_decode(list, '[1, 2.3]', [1,2.3])
        
    def test_classes(self):
        self.assert_decode(SimpleArgs, '{"a": 1, "c": 3, "b": 2}', SimpleArgs(1, 2, 3))
        self.assert_decode(NamedArgs, '{"q": 2, "p": 1}', NamedArgs(1, 2))
        self.assert_decode(MixedArgs, '{"y": 2, "x": 1}', MixedArgs(1, 2))
        
    def test_choice(self):
        self.assert_decode(Choice(NamedArgs, MixedArgs), '{"q": 2, "p": 1}', NamedArgs(1, 2))
        self.assert_decode(Choice(NamedArgs, MixedArgs), '{"y": 2, "x": 1}', MixedArgs(1, 2))
        
    def test_nested(self):
        self.assert_decode(TypedArgs, 
                           '{"y": {"a": 1, "c": 3, "b": 2}, "x": {"q": 2, "p": 1}}', 
                           TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)))
        
    def test_named_tuple(self):
        NT = namedtuple('NT', 'a, b')
        self.assert_decode(NT(int, str), '{"a": 1, "b":"two"}', NT(1, 'two'))

        
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
        assert result == target, result  
    
    def test_native(self):
        self.assert_encode('abc', '"abc"')
        self.assert_encode([1,2.3], '[1, 2.3]')
        
    def test_classes(self):
        self.assert_encode(SimpleArgs(1, 2, 3), '{"a": 1, "c": 3, "b": 2}')
        self.assert_encode(NamedArgs(1, 2), '{"q": 2, "p": 1}')
        self.assert_encode(MixedArgs(1, 2), '{"y": 2, "x": 1}')
        
    def test_nested(self):
        self.assert_encode(TypedArgs(NamedArgs(1, 2), SimpleArgs(1, 2, 3)), 
                           '{"y": {"a": 1, "c": 3, "b": 2}, "x": {"q": 2, "p": 1}}')
