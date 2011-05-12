
from collections import OrderedDict
from string import whitespace

import pytyp.spec.abcs as abcs
from pytyp.spec.check import checked as _checked, verify as _verify
from pytyp.spec.abcs import normalize, ANY


RESIZE = '__'


def record(typename, field_names, verbose=False, mutable=False, checked=True,
           context=None):
    if context is None: context = abcs.__dict__
    nsd = parse_args(field_names, context)
    template = class_template(typename, nsd, mutable, checked)
    if verbose: print(template)
    namespace = dict(property=property, checked=_checked, verify=_verify)
    namespace.update(context)
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
    properties = '\n'.join(map(pad4, fmt_properties(nsd, mutable)))
    block_mutable_dict = ''
    return '''
class {typename}(dict, {typespec}):
    """
    record {typename}:
{class_doc}
    """
    __specs = {class_specs}
    {checked}
    def __init__(self, {init_args}):
{init_set}
        self.__lock = None
    def __setitem__(self, name, value):
        if name not in self.__specs and '__' not in self.__specs:
            raise TypeError('Record {{}} does not exist'.format(name))
{verify}            
        super().__setitem__(name, value)
{properties}
    def _replace(self, **kargs):
        state = dict(self)
        state.update(kargs)
        return {typename}(**state)
    def __setattr__(self, name, value):
        if hasattr(self, '_{typename}__lock'):
            self.__setitem__(name, value)
        super().__setattr__(name, value)
{block_mutable_dict}
'''.format(**locals())


def left(n):
    pad = ' ' * n
    def padder(line):
        return pad + line
    return padder


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
            if not isinstance(name, int):
                yield '{}={}'.format(name, spec)
    return 'And(Rec({}),Atr({}))'.format(','.join(fmt_rec()), ','.join(fmt_atr()))


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
    yield 'super().__init__(**kargs)'
    

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
