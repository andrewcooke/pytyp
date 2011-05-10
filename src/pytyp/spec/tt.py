
from collections import _iskeyword
from string import whitespace

from pytyp.spec.abcs import And, Ins, Rec
from pytyp.spec.check import checked as _checked, verify as _verify


def record(typename, field_names, verbose=False, rename=False, mutable=False, 
           checked=False):
    validate_name(typename)
    nds = validate_args(parse_args(field_names), rename=rename)
    template = class_template(typename, list(nds), mutable, checked)
    if verbose: print(template)
    namespace = dict(property=property, checked=_checked, verify=_verify, 
                     And=And, Ins=Ins, Rec=Rec)
    try:
        exec(template, namespace)
    except SyntaxError as e:
        raise SyntaxError(e.msg + ':\n\n' + template)
    return namespace[typename]
    

def class_template(typename, nds, mutable, checked):
    pad4, pad8, pad12 = left(4), left(8), left(12)
    args_specs = ','.join('{}={}'.format(name, spec) for (name, _, spec) in nds)
    class_specs = '{' + ','.join(fmt_class_specs(nds)) + '}'
    class_doc = '\n'.join(map(pad8, fmt_init_args(nds)))
    checked = '@checked' if checked else ''
    verify = pad8('else: verify(value, self.__specs[name])') if checked else ''
    init_args = ', '.join(fmt_init_args(nds))
    init_set = '\n'.join(pad8('self.__dict["{name}"] = {name}'.format(name=name))
                         for (name, _, _) in nds)
    properties = '\n'.join(map(pad4, fmt_properties(nds, mutable)))
    return '''
class {typename}(Ins(Rec,{args_specs})):
    """record {typename}:
{class_doc}"""
    __specs = {class_specs}
    {checked}
    def __init__(self, {init_args}):
        self.__dict = {{}}
{init_set}
        self.__locked = True
    def __getitem__(self, name):
        return self.__dict[name]
    def __setitem__(self, name, value):
        if name not in self.__specs:
            raise TypeError('Record {{}} does not exist'.format(name))
{verify}            
        self.__dict[name] = value
{properties}
    def _replace(self, **kargs):
        state = dict(self.__dict)
        state.update(kargs)
        return {typename}(**state)
    def __setattr__(self, name, value):
        if hasattr(self, '_{typename}__locked'):
            self.__setitem__(name, value)
        super().__setattr__(name, value)
'''.format(**locals())


def left(n):
    pad = ' ' * n
    def padder(line):
        return pad + line
    return padder


def fmt_class_specs(nds):
    for (name, _, spec) in nds:
            yield '"{name}":{spec}'.format(**locals())


def fmt_init_args(nds):
    for (name, default, spec) in nds:
        if default is None:
            yield '{name}:{spec}'.format(**locals())
    for (name, default, spec) in nds:
        if default is not None:
            yield '{name}:{spec}={default}'.format(**locals())


def fmt_properties(nds, mutable):
    for (name, default, spec) in nds:
        p = property()
        yield '@property'
        yield 'def {name}(self) -> {spec}: return self.__dict["{name}"]'.format(**locals())
        if mutable:
            yield '@{name}.setter'.format(**locals())
            yield 'def {name}(self, value:{spec}): self.__dict["{name}"] = value'.format(**locals())
        
        
def parse_args(args):
    '''
    >>> list(parse_args('a,b'))
    [('a', None, 'Any'), ('b', None, 'Any')]
    >>> list(parse_args('a:Seq b'))
    [('a', None, 'Seq'), ('b', None, 'Any')]
    >>> list(parse_args('a=[1,2]:Seq(int) b=3'))
    [('a', '[1,2]', 'Seq(int)'), ('b', '3', 'Any')]
    >>> list(parse_args('a:Seq({x:y) b, c:foo'))
    Traceback (most recent call last):
      ...
    ValueError: Cannot parse a:None:Seq({x:y) b, c:foo
    '''
    open_to_close = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
    parens, words, default = [], [''], False
    gap_state, NO, GAP, NEXT = 0, 0, 1, 2
    args = args.strip()
    while args:
        (c, args) = args[0], args[1:]
        if parens:
            if c in open_to_close:
                parens.append(c)
            elif c == open_to_close[parens[-1]]:
                parens.pop()
            words[-1] = words[-1] + c
        else:
            if c in whitespace + ',':
                if gap_state is NO:
                    gap_state = GAP
            elif c == '=':
                if default:
                    raise ValueError('Double default near {}'.format(args))
                if len(words) != 1:
                    raise ValueError('Default must follow name near '.format(args))
                words.append('')
                default, gap_state = True, NEXT
            elif c == ':':
                if not default and len(words) == 1:
                    words.append(None)
                words.append('')
                gap_state = NEXT
            elif gap_state == GAP:
                if len(words) == 1: words.append(None)
                if len(words) == 2: words.append('Any')
                yield tuple(words)
                words, default, gap_state = [c], False, NO
            elif c in open_to_close:
                parens.append(c)
                words[-1] = words[-1] + c
                gap_state = NO
            else:
                words[-1] = words[-1] + c
                gap_state = NO
    if parens:
        raise ValueError('Cannot parse {}'.format(':'.join(map(str, words))))
    elif words[0]:
        if len(words) == 1: words.append(None)
        if len(words) == 2: words.append('Any')
        yield tuple(words)
        

def validate_args(args, rename=False):
    names = set()
    for (i, (name, default, spec)) in enumerate(args):
        for i, name in enumerate(names):
            if rename and \
                    (not all(c.isalnum() or c=='_' for c in name) or _iskeyword(name)
                     or not name or name[0].isdigit() or name.startswith('_')
                     or name in names):
                names[i] = '_%d' % i
        if name in names:
            raise ValueError('Duplicate name: {}'.format(name))
        validate_name(name)
        yield (name, default, spec)

        
def validate_name(name):
    if not all(c.isalnum() or c=='_' for c in name):
        raise ValueError(
            'Type names and field names can only contain alphanumeric '
            'characters and underscores: {!r}'.format(name))
    if _iskeyword(name):
        raise ValueError(
            'Type names and field names cannot be a keyword: {!r}'.format(name))
    if name[0].isdigit():
        raise ValueError(
            'Type names and field names cannot start with a '
            'number: {!r}'.format(name))
    


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
