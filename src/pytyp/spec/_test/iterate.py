

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
        
        