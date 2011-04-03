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

