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

from collections import OrderedDict
from string import whitespace

from pytyp.spec.check import checked as _checked, verify as _verify
from pytyp.spec.abcs import normalize, ANY
import pytyp.spec.abcs as abcs


RESIZE = '__'


class RecordException(TypeError): pass


def record(typename, field_names, verbose=False, mutable=False, checked=True,
           context=None):
    '''
    This creates a wrapper around `dict` that allows attribute access.  In other
    words: it unifies `Rec()` and `Atr()`; it provides both __..item__ and __..attr__
    access.
    
    :param typename: The name of the class to be created.
    :param field_names: An argument list in normal Python syntax.  This can
                        include  default values and type annotations.  For example:
                        'a,b=5' or 'a:int,b:Seq(str)'.
    :param verbose: (default False) If True the source will be printed to stdout.
    :param mutable: (default False) If True contents can be changed; it False the
                    instance can be hashed.
    :param checked: (default True) If True, initial arguments and future modifications
                    (if any) are checked against type specifications (if given in
                    ``field_names``).
    :param context: (default None) A ``dict`` that can provide access to additional
                    names used in ``field_names``.  The ``pytyp.spec.abcs`` module
                    is always available.
                    
    Here are some examples::
    
        >>> MyTuple = record('MyTuple', ',') # no names or types - like a tuple
        >>> t = MyTuple(1,2)
        >>> t[0]
        1
        >>> t._1 # attribute access to indexed fields
        2
        >>> hash(t)
        7114083200724408387
        
        >>> Record = record('Record', 'a:str,b:int=7', mutable=True)
        >>> r = Record('foo')
        >>> r.b
        7
        >>> r.b = 41
        >>> r['a'] = 42
        Traceback (most recent call last):
          ...
        TypeError: Type str inconsistent with 42.
        
        >>> Variable = record('Variable', '__:int')
        >>> v = Variable(a=1,b=2,c=3)
        >>> len(v)
        3
    '''
    _context = dict(abcs.__dict__)
    if context: _context.update(context)
    nsd = parse_args(field_names, _context)
    template = class_template(typename, nsd, mutable, checked)
    if verbose: print(template)
    namespace = dict(property=property, checked=_checked, verify=_verify)
    namespace.update(_context)
    try:
        exec(template, namespace)
    except SyntaxError as e:
        raise SyntaxError(e.msg + ':\n\n' + template)
    return namespace[typename]
    

def class_template(typename, nsd, mutable, checked):
    pad4, pad8, pad12 = left(4), left(8), left(12)
    typespec = fmt_typespec(nsd)
    class_specs = '{' + ','.join(fmt_class_specs(nsd)) + '}'
    class_doc = '\n'.join(map(pad8, fmt_init_args(nsd)))
    checked = '@checked' if checked else ''
    verify = '\n'.join(map(pad8, fmt_verify(nsd, checked)))
    init_args = ', '.join(fmt_init_args(nsd))
    init_set = '\n'.join(map(pad8, fmt_init_set(nsd)))
    immutable = '' if mutable else fmt_immutable()
    return '''class {typename}(dict, {typespec}):
    """
    record {typename}:
{class_doc}
    """
    __specs = {class_specs}
    {checked}
    def __init__(self, {init_args}):
{init_set}
        self.__hash = []
        self._lock = None
    def __setitem__(self, name, value):
        if not {mutable}: raise TypeError('Immutable')
        if name not in self.__specs and '__' not in self.__specs:
            raise TypeError('Record {{}} does not exist'.format(name))
{verify}            
        super().__setitem__(name, value)
    def _replace(self, **kargs):
        state = dict(self)
        state.update(kargs)
        return {typename}(**state)
    def __unpack(self, name):
        if name.startswith('_'):
            try: return int(name[1:])
            except: pass
        return name
    def __getattr__(self, name):
        if name != '_lock' and hasattr(self, '_lock'):
            return self.__getitem__(self.__unpack(name))
        return super().__getattr__(name)
    def __setattr__(self, name, value):
        if hasattr(self, '_lock'):
            if not {mutable}: raise AttributeError('Immutable')
            self.__setitem__(name, value)
        super().__setattr__(name, value)
    def __delattr__(self, name):
        # could delete additional fields
        raise RecordException('Cannot delete from record')
    def __delitem__(self, name):
        # could delete additional fields
        raise RecordException('Cannot delete from record')
    def fromkeys(self, *args):
        raise RecordException('Not supported in record')
    def pop(self, *args):
        raise RecordException('Not supported in record')
    def popitem(self, *args):
        raise RecordException('Not supported in record')
    def setdefault(self, *args):
        raise RecordException('Not supported in record')
    def update(self, *args):
        raise RecordException('Not supported in record')
{immutable}'''.format(**locals())


def left(n):
    pad = ' ' * n
    def padder(line):
        return pad + line
    return padder


def fmt_immutable():
    return '''
    def __hash__(self):
        if not self.__hash:
            self.__hash.append(hash(tuple((name, value) for (name, value) in self.items())))
        return self.__hash[0]'''
    

def fmt_verify(nsd, checked):
    if checked:
        yield "spec = self.__specs.get(name, self.__specs.get('__'))"
        yield "verify(value, spec)"


def fmt_typespec(nsd):
    def fmt_rec():
        for (name, (spec, _)) in nsd.items():
            if isinstance(name, int):
                yield str(spec)
        for (name, (spec, _)) in nsd.items():
            if not isinstance(name, int):
                yield '{}={}'.format(name, spec)
    def fmt_atr():
        for (name, (spec, _)) in nsd.items():
            if isinstance(name, int):
                yield '{}={}'.format(to_arg(name), spec)
        for (name, (spec, _)) in nsd.items():
            if not isinstance(name, int) and name != RESIZE:
                yield '{}={}'.format(name, spec)
    if len(nsd) - (1 if RESIZE in nsd else 0):
        return 'And(Rec({}),Atr({}))'.format(','.join(fmt_rec()), ','.join(fmt_atr()))
    else:
        return 'Rec({})'.format(','.join(fmt_rec()))


def fmt_class_specs(nsd):
    for (name, (spec, _)) in nsd.items():
            yield '{name!r}:{spec}'.format(**locals())


def to_arg(name):
    if isinstance(name, int):
        return '_' + str(name)
    else:
        return name


def fmt_init_args(nsd):
    for (name, (spec, default)) in nsd.items():
        if default is None and name != RESIZE:
            arg = to_arg(name)
            yield '{arg}:{spec}'.format(**locals())
    for (name, (spec, default)) in nsd.items():
        if default is not None and name != RESIZE:
            arg = to_arg(name)
            yield '{arg}:{spec}={default}'.format(**locals())
    if RESIZE in nsd:
        if nsd[RESIZE][1] is not None:
            raise TypeError('Cannot specify a default value for __')
        yield '**kargs:Rec(__={})'.format(nsd[RESIZE][0])
            
            
def fmt_init_set(nsd):
    if RESIZE in nsd:
        yield 'kargs = dict(kargs)'
    else:
        yield 'kargs = {}'
    for (name, (_, _)) in nsd.items():
        if name != RESIZE:
            yield 'kargs[{name!r}] = {arg}'.format(arg=to_arg(name), name=name)
    yield 'super().__init__(kargs)'
    

def fmt_properties(nsd, mutable):
    for (name, (spec, default)) in nsd.items():
        if name != RESIZE:
            arg = to_arg(name)
            p = property()
            yield '@property'
            yield 'def {arg}(self) -> {spec}: return self[{name!r}]'.format(**locals())
            if mutable:
                yield '@{arg}.setter'.format(**locals())
                yield 'def {arg}(self, value:{spec}): self[{name!r}] = value'.format(**locals())
        
        
def parse_args(args, context):
    '''
    Parse a comma-separated list of
       name : spec = default
    triples, where all fields are optional, but the separators are required if
    the field to the right exists.
    '''
    open_to_close = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
    NO, OPEN, LEADING = 0, 1, 2
    def each(args):
        # trailing space at end catches trailing comma
        count, used, c, args = 0, '', '', args.strip() + ' '
        def syntax_error():
            raise ValueError('Cannot parse: {}[{}]'.format(used, c+args))
        while args:
            parens, words, gap = [], [''], NO
            while args:
                used, c, args = used + c, args[0], args[1:]
                if parens:
                    if c == open_to_close[parens[-1]]:
                        parens.pop()
                    elif c in open_to_close:
                        parens.append(c)
                    words[-1] = words[-1] + c
                else:
                    if c == ',':
                        break
                    if c in whitespace:
                        if gap is NO: gap = OPEN
                    elif c == ':':
                        if len(words) > 1: syntax_error()
                        while len(words) < 2: words.append('')
                        gap = LEADING
                    elif c == '=':
                        if len(words) > 2: syntax_error()
                        while len(words) < 3: words.append('')
                        gap = LEADING
                    elif gap == OPEN:
                        syntax_error()
                    elif c in open_to_close:
                        parens.append(c)
                        words[-1] = words[-1] + c
                        gap = NO
                    else:
                        words[-1] = words[-1] + c
                        gap = NO
            if parens:
                syntax_error()
            if words[0] == '': # have numbered argument
                words[0] = count
                count += 1 
            if len(words) == 1: words.append('')
            if words[1] == '':
                words[1] = ANY
            else:
                globals = dict(context)
                exec('spec=normalize(' + words[1] + ')', globals)
                words[1] = globals['spec']
            if len(words) == 2: words.append(None)
            if words[2] == '': words[1] = None
            if len(words) > 3: syntax_error()
            yield tuple(words)
    return OrderedDict((nsd[0], (nsd[1], nsd[2])) for nsd in each(args))    


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
