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

from inspect import getcallargs, getfullargspec
from functools import wraps

from pytyp.spec.abcs import type_error, normalize


def verify(value, spec):
    '''
    If ``value`` is *not* an instance of ``spec`` then raise a ``TypeError``.
    '''
    spec = normalize(spec)
    if not isinstance(value, spec):
        type_error(value, spec)
        
        
def verify_all(callargs, annotations):
    '''
    Helper to verify a set of values against the appropriate type annotations.sy
    '''
    for name in annotations:
        spec = annotations[name]
        try:
            verify(callargs.get(name), spec)
        except AttributeError:
            pass
    
        
def unpack(func):
    '''
    Separate the return specification from the rest.
    '''
    annotations = dict((name, normalize(spec))
                       for (name, spec) in getfullargspec(func).annotations.items())
    try:
        rspec = annotations.pop('return')
        do_return = True
    except KeyError:
        rspec = None
        do_return = False
    return (annotations, do_return, rspec)


def checked(func):
    '''
    A decorator that adds runtime verification of type annotations to a
    function or method.

      >>> @checked
      ... def str_len(s:str) -> int:
      ...     return len(s)
      >>> str_len('abc')
      3
      >>> str_len([1,2,3])
      Traceback (most recent call last):
        ...
      TypeError: Type str inconsistent with [1, 2, 3].
      >>> @checked
      ... def bad_len(s:str) -> int:
      ...     return 'wrong'
      >>> bad_len('abc')
      Traceback (most recent call last):
        ...
      TypeError: Type int inconsistent with 'wrong'.
    '''
    (annotations, do_return, rspec) = unpack(func)
    @wraps(func)
    def wrapper(*args, **kargs):
        callargs = getcallargs(func, *args, **kargs)
        verify_all(callargs, annotations)
        result = func(*args, **kargs)
        if do_return:
            verify(result, rspec)
        return result
    return wrapper


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
