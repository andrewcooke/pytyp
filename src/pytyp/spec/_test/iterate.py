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

from pytyp.spec.abcs import Seq, Opt, Sum


#def callback9(current, vsn):
#    for (value, spec, name) in vsn:
#        try:
#            contents = spec._for_each(value, callback9)
#            yield '[{}:{}]'.format(spec, ';'.join(contents))
#        except AttributeError:
#            yield str(value)
#
#def show9(container, spec):
#    return next(callback9(None, [(container, spec, None)]))
#
#
#def group(spec, descriptions):
#    return '[{}:{}]'.format(spec, ';'.join(descriptions))
#
#
#def callback1(current, vsn):
#    for (value, spec, name) in vsn:
#        try:
#            yield group(spec, spec._for_each(value, callback1))
#        except AttributeError:
#            yield str(value)
#
#def show1(value, spec):
#    return group(spec, spec._for_each(value, callback1))
#
#def callback2(current, vsn):
#    if issubclass(current, Sum):
#        for (value, spec, name) in vsn:
#            try:
#                if isinstance(value, spec):
#                    yield group(spec, spec._for_each(value, callback2))
#                    return
#            except TypeError:
#                pass
#    else:
#        for (value, spec, name) in vsn:
#            try:
#                yield group(spec, spec._for_each(value, callback2))
#            except AttributeError:
#                yield str(value)
#        
#
#def show2(value, spec):
#    return group(spec, spec._for_each(value, callback2))


def format1(v, s):
    try:
        return s._for_each(v, callback1)
    except AttributeError:
        return str(v)

def callback1(current, vsn):
    return '[{}:{}]'.format(current, ';'.join(format1(v, s) for (v, s, _) in vsn))

def show1(value, spec):
    return spec._for_each(value, callback1)


def format2(v, s):
    try:
        return s._for_each(v, callback2)
    except AttributeError:
        return str(v)

def callback2(current, vsn):
    if issubclass(current, Sum):
        for (v, s, _) in vsn:
            try:
                if isinstance(v, s): return '[{}:{}]'.format(current, format2(v, s))
            except TypeError:
                pass
    else:
        return '[{}:{}]'.format(current, ';'.join(format2(v, s) for (v, s, _) in vsn))

def show2(value, spec):
    return spec._for_each(value, callback2)


def format3(v, s):
    if not isinstance(v, s): raise TypeError
    try:
        return s._backtrack(v, callback3)
    except AttributeError:
        return str(v)

def callback3(current, vsn):
    return '[{}:{}]'.format(current, ';'.join(format3(v, s) for (v, s, _) in vsn))

def show3(value, spec):
    return spec._backtrack(value, callback3)


class IterationTest(TestCase):
    
    def assert_show(self, f, value, spec, target):
        result = f(value, spec)
        assert result == target, result
    
    def test_show1(self):
        self.assert_show(show1, [1,2,3], Seq(int), 
                         '[Seq(int):[int:1];[int:2];[int:3]]')
        self.assert_show(show1, [[1,2],('one','two')], Seq(Seq()), 
                         '[Seq(Seq(Cls(object))):[Seq(Cls(object)):[Cls(object):1];[Cls(object):2]];[Seq(Cls(object)):[Cls(object):one];[Cls(object):two]]]')
        try:
            self.assert_show(show1, [1,2,None], Seq(Opt(int)), '')
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_show2(self):
        self.assert_show(show2, [1,2,3], Seq(int), 
                         '[Seq(int):[int:1];[int:2];[int:3]]')
        self.assert_show(show2, [[1,2],('one','two')], Seq(Seq()), 
                         '[Seq(Seq(Cls(object))):[Seq(Cls(object)):[Cls(object):1];[Cls(object):2]];[Seq(Cls(object)):[Cls(object):one];[Cls(object):two]]]')
        self.assert_show(show2, [1,2,None], Seq(Opt(int)), '[Seq(Opt(int)):[Opt(int):[int:1]];[Opt(int):[int:2]];[Opt(int):[Cls(NoneType):None]]]')
        
    def test_show3(self):
        self.assert_show(show3, [1,2,3], Seq(int), 
                         '[Seq(int):[int:1];[int:2];[int:3]]')
        self.assert_show(show3, [[1,2],('one','two')], Seq(Seq()), 
                         '[Seq(Seq(Cls(object))):[Seq(Cls(object)):[Cls(object):1];[Cls(object):2]];[Seq(Cls(object)):[Cls(object):one];[Cls(object):two]]]')
        self.assert_show(show3, [1,2,None], Seq(Opt(int)), '[Seq(Opt(int)):[Opt(int):[int:1]];[Opt(int):[int:2]];[Opt(int):[Cls(NoneType):None]]]')
        
        