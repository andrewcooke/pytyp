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

from inspect import getfullargspec, getcallargs
from collections import Callable, Iterable, Mapping
from pytyp.spec.abcs import Atomic, ANY, Rec, Seq, Cls, type_error, Alt, \
    Sub, normalize
from pytyp.spec.dispatch import overload


def encode(obj, raw=Atomic, recurse=True, check_circular=True, 
           strict=True):
    '''
    Encode a Python class as a dictionary.  This function can also encode
    lists, tuples and dictionaries containing classes, and nested classes.

    :param obj: The object to be encoded.
    :param raw: ABC for types that are not explicitly encoded, but passed 
                through as raw values.
    :param recurse: Recursively encode values?  `encode` is designed to be
                    used with other encoders; sometimes these expect only
                    a single value to be encoded (`recurse=False`).
    :param check_circular: If `True`, an error is rased for circular
                           references (if disabled the encoding may loop
                           indefinitely).
    :param strict: If `True`, fail when constructor parameters with default
                   values have no corresponding attribute.
    :return: A set of Python dicts and lists that encode `raw` in a format
             suitable for output in JSON, YAML, etc.
    '''
    
    if isinstance(obj, raw):
        return obj
    
    # replace with generic block?
    if check_circular is True:
        check_circular = set([id(obj)])
    elif check_circular:
        if id(obj) in check_circular:
            raise ValueError('Circular reference at {0}'.format(obj))
        else:
            check_circular.add(id(obj))
            
    encode_ = lambda o: encode(o, raw=raw, recurse=recurse, 
                               check_circular=check_circular, strict=strict)
    
    if isinstance(obj, list):
        return list(map(encode_, obj))
    
    if isinstance(obj, tuple):
        return tuple(map(encode_, obj))
    
    if isinstance(obj, dict):
        return dict((name, encode_(obj[name])) for name in obj)
    
    spec = getfullargspec(obj.__class__.__init__)
        
    def check(name, eq, type_):
        value = getattr(obj, name)
        if isinstance(value, type_) != eq:
            raise TypeError('{0} for {1} is {2} of type {3}'.format(
                    name, type(obj), '' if eq else 'not ', type_))
        if recurse:
            value = encode_(value)
        return (name, value)
    
    def unpack_dict():
        for name in spec.args[1:]: # skip self
            # reject Callable to catch the common case of methods
            yield check(name, False, Callable)
        try:
            if spec.varkw:
                (_, kargs) = check(spec.varkw, True, dict)
                for (name, value) in kargs.items():
                    yield (name, value)
        except AttributeError:
            if strict: raise
        try:
            for name in spec.kwonlyargs:
                yield check(name, False, Callable)
        except AttributeError:
            if strict: raise
            
    if spec.varargs:
        raise TypeError('Cannot encode *args in a map (no names!)')

    return dict(unpack_dict())


def class_to_dict_spec(cls):
    '''
    Create a type specification for a dict, given one for a class.  This 
    reads any type annotation in the constructor, adds positional args as required, 
    and adds keyword args (with defaults) as optional.
    
    :param cls: The class to encode
    :return: `(varargs, varkw, spec)` where `varargs` is the name of the `*args`
             parameter (or `None`); `varkw` is the name of the `**kargs` 
             parameter (or `None`) and `spec` is the type specification.
    
    >>> class Example():
    ...     def __init__(self, pos, ann:str, ann_deflt:int=42, *varargs, kwonly, kwonly_deflt='value', **varkw):
    ...         pass
    >>> #class_to_dict_spec(Example)
    #('varargs', 'varkw', {Opt('ann_deflt'): <class 'int'>, 'ann': <class 'str'>, 'pos': None, Opt('kwonly_deflt'): None, Opt('varargs'): None, Opt('varkw'): None, 'kwonly': None})
    '''
    argspec = getfullargspec(cls._abc_class.__init__)
    newspec = {}
    names = set()
    # types defined by user
    if argspec.annotations:
        for name in argspec.annotations:
            if name != 'return' and name != 'self':
                if name not in (argspec.varargs, argspec.varkw):
                    key = name
                    newspec[key] = normalize(argspec.annotations[name])
                    names.add(name)
    # other args with default are optional
    if argspec.defaults:
        for name in argspec.args[-len(argspec.defaults):]:
            if name not in names:
                newspec[Rec.OptKey(name)] = ANY
            else:
                newspec[Rec.OptKey(name)] = newspec.pop(name)
            names.add(name)
    # other args are required
    if argspec.args:
        for name in argspec.args:
            if name not in names and name != 'self':
                newspec[name] = ANY
                names.add(name)
    if argspec.kwonlyargs:
        for name in argspec.kwonlyargs:
            if name not in names:
                if argspec.kwonlydefaults and name in argspec.kwonlydefaults:
                    newspec[Rec.OptKey(name)] = ANY
                else:
                    newspec[name] = ANY
                names.add(name)
    # we can't express args in terms of Rec, but we can carry across kargs
    if argspec.varargs:
        raise TypeError('Cannot convert a *args specification to a dict (use **kargs)')
    if argspec.varkw:
        if argspec.varkw in argspec.annotations:
            oldspec = normalize(argspec.annotations[argspec.varkw])
            if issubclass(oldspec, Rec):
                newspec.update(oldspec._to_dict())
            else:
                raise TypeError('**kargs specification was not Rec()')
        else:
            newspec['__'] = ANY
#    # *args and **kargs are optional
#    if argspec.varargs and argspec.varargs not in names:
#        newspec[Rec.OptKey(argspec.varargs)] = Seq(ANY)
#    if argspec.varkw and argspec.varkw not in names:
#        newspec[Rec.OptKey(argspec.varkw)] = Rec(__=ANY)
    return (argspec.varargs, argspec.varkw, Rec(_dict=newspec))


# decode starts w single spec/value.
# transcode handles single value - either rewrites or calls expand.
# expand needs a callback for multiple values.  so transcode needs to 
# pass in a callback that (1) calls transcode for each in turn and 
# (2) assembles the data correctly.

class Transcode:
    
    @overload
    def __call__(self, value, spec):
        if isinstance(value, spec):
            return value
        else:
            type_error(value, spec)

    @__call__.intercept
    def map_instance(self, value:Mapping, spec:Sub(Cls)):
        (varargs, varkw, dict_spec) = class_to_dict_spec(spec)
        new_value = transcode(value, dict_spec)
        args = new_value.pop(Rec.OptKey(varargs), []) if varargs else []
        kargs = new_value.pop(Rec.OptKey(varkw), {}) if varkw else {}
        args.extend(new_value.pop(index) 
                    for index in sorted(key 
                        for key in new_value.keys() 
                        if isinstance(Rec.OptKey.unpack(key), int)))
        kargs.update((Rec.OptKey.unpack(key), value) 
                     for (key, value) in new_value.items())    
        return spec._abc_class(*args, **kargs)
    
    @__call__.intercept
    def other_instance(self, value, spec:Sub(Cls)):
        if isinstance(value, spec):
            return value
        else:
            type_error(value, spec)
            
    @__call__.intercept
    def sequence(self, value, spec:Sub(Seq)):
        return list(spec._for_each(value, lambda c, vsn: (transcode(v, s) for (v, s, n) in vsn)))
    
    @__call__.intercept
    def record(self, value, spec:Sub(Rec)):
        if spec._int_keys():
            return tuple(spec._for_each(value, 
                        lambda c, vsn: (transcode(v, s) 
                                        for (v, s, n) in sorted(vsn, 
                                            key=lambda vsn: Rec.OptKey.unpack(vsn[2])))))
        else:
            return dict(spec._for_each(value, 
                        lambda c, vsn: ((n, transcode(v, s)) for (v, s, n) in vsn)))
            
    @__call__.intercept
    def alternative(self, value, spec:Sub(Alt)):
        def alt(c, vsn):
            error = None
            for (v, s, _) in vsn:
                try:
                    return transcode(v, s)
                except TypeError as e:
                    error = e
            raise error
        return spec._for_each(value, alt)
    
transcode = Transcode()


class Transcode3:
    
    @overload
    def __call__(self, value, spec):
        if isinstance(value, spec):
            return value
        else:
            type_error(value, spec)

    @__call__.intercept
    def map_instance(self, value:Mapping, spec:Sub(Cls)):
        (varargs, varkw, dict_spec) = class_to_dict_spec(spec)
        new_value = transcode3(value, dict_spec)
        args = new_value.pop(Rec.OptKey(varargs), []) if varargs else []
        kargs = new_value.pop(Rec.OptKey(varkw), {}) if varkw else {}
        args.extend(new_value.pop(index) 
                    for index in sorted(key 
                        for key in new_value.keys() 
                        if isinstance(Rec.OptKey.unpack(key), int)))
        kargs.update((Rec.OptKey.unpack(key), value) 
                     for (key, value) in new_value.items())    
        return spec._abc_class(*args, **kargs)
    
    @__call__.intercept
    def other_instance(self, value, spec:Sub(Cls)):
        if isinstance(value, spec):
            return value
        else:
            type_error(value, spec)
            
    @__call__.intercept
    def sequence(self, value, spec:Sub(Seq)):
        return list(spec._for_each(value, lambda c, vsn: (transcode3(v, s) for (v, s, n) in vsn)))
    
    @__call__.intercept
    def record(self, value, spec:Sub(Rec)):
        if spec._int_keys():
            return tuple(spec._for_each(value, 
                        lambda c, vsn: (transcode3(v, s) 
                                        for (v, s, n) in sorted(vsn, 
                                            key=lambda vsn: Rec.OptKey.unpack(vsn[2])))))
        else:
            return dict(spec._for_each(value, 
                        lambda c, vsn: ((n, transcode3(v, s)) for (v, s, n) in vsn)))
            
    @__call__.intercept
    def alternative(self, value, spec:Sub(Alt)):
        def alt(c, vsn):
            error = None
            for (v, s, _) in vsn:
                try:
                    return transcode3(v, s)
                except TypeError as e:
                    error = e
            raise error
        return spec._for_each(value, alt)
    
transcode3 = Transcode3()


def transcode2(value, spec):
    if issubclass(spec, Cls) and spec._abc_class != object:
        if isinstance(value, Mapping):
            (varargs, varkw, dict_spec) = class_to_dict_spec(spec)
            new_value = transcode(value, dict_spec)
            args = new_value.pop(Rec.OptKey(varargs), []) if varargs else []
            kargs = new_value.pop(Rec.OptKey(varkw), {}) if varkw else {}
            args.extend(new_value.pop(index) 
                        for index in sorted(key 
                            for key in new_value.keys() 
                            if isinstance(Rec.OptKey.unpack(key), int)))
            kargs.update((Rec.OptKey.unpack(key), value) 
                         for (key, value) in new_value.items())    
            return spec._abc_class(*args, **kargs)
        elif isinstance(value, spec):
            return value
        else:
            type_error(value, spec)
    elif issubclass(spec, Seq):
        return list(spec._for_each(value, lambda c, vsn: (transcode(v, s) for (v, s, n) in vsn)))
    elif issubclass(spec, Rec):
        if spec._int_keys():
            return tuple(spec._for_each(value, 
                        lambda c, vsn: (transcode(v, s) 
                                        for (v, s, n) in sorted(vsn, 
                                            key=lambda vsn: Rec.OptKey.unpack(vsn[2])))))
        else:
            return dict(spec._for_each(value, 
                        lambda c, vsn: ((n, transcode(v, s)) for (v, s, n) in vsn)))
    elif issubclass(spec, Alt):
        def alternative(c, vsn):
            error = None
            for (v, s, _) in vsn:
                try:
                    return transcode(v, s)
                except TypeError as e:
                    error = e
            raise error
        return spec._for_each(value, alternative)
    elif isinstance(value, spec):
        return value
    else:
        type_error(value, spec)


def decode(value, spec):
    '''
    Decode a dictionary of data as a Python class.  This function can also 
    decode lists, tuples and dictionaries of values, and nested values.

    :param value: The data to decode.
    :param spec: The class (more generally, the type specification - see
                 below) to create.
    :result: A set of Python objects structured as `spec`, containing the
             data from `value`.
    '''
    return transcode(value, normalize(spec))


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())

