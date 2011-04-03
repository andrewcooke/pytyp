
_BORING = dir(type('dummy', (object,), {}))


class AttributeEquality():
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        def to_dict(obj):
            return dict((name, getattr(obj, name))
                        for name in dir(obj)
                        if name not in _BORING)
        return to_dict(self) == to_dict(other)


class SimpleArgs(AttributeEquality):
    
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        

class NamedArgs(AttributeEquality):
    
    def __init__(self, p=None, q=None):
        self.p = p
        self.q = q
        
        
class MixedArgs(AttributeEquality):
    
    def __init__(self, x, y=None):
        self.x = x
        self.y = y
        

class TypedArgs(AttributeEquality):
    
    def __init__(self, x:NamedArgs, y:SimpleArgs=None) -> int:
        self.x = x
        self.y = y
        
        
class ArgsAndKArgs(AttributeEquality):
    
    def __init__(self, *simples:[SimpleArgs], **untyped):
        self.simples = simples
        self.untyped = untyped
        

class MissingKArgs(AttributeEquality):
    
    def __init__(self, *simples:[SimpleArgs], **untyped):
        self.simples = simples
        self._untyped = untyped
        

class TypedKArgs(AttributeEquality):
    
    def __init__(self, **kargs:{'foo': SimpleArgs}):
        self.kargs = kargs
        

class User():
    
    def __init__(self, name, email):
        self.name = name
        self.email = email


class Permission():
    
    def __init__(self, resource, rw):
        self.resource = resource
        self.rw = rw


class Config():
    
    def __init__(self, users:[User], permission:Permission):
        self.users = users
        self.permission = permission

