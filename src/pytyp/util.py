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

from functools import wraps
from reprlib import get_ident


_BORING = dir(type('dummy', (object,), {}))

def items(obj):
    for name in dir(obj):
        if name not in _BORING:
            yield (name, getattr(obj, name))


def make_recursive_block(make_key=lambda args: id(args[0]), 
                         on_recursion=lambda x: x):

    def recursive_block(function):

        running = set()
    
        @wraps(function)
        def wrapper(*args):
            subkey = make_key(args)
            key = (subkey, get_ident())
            if key in running:
                return on_recursion(subkey)
            running.add(key)
            try:
                result = function(*args)
            finally:
                running.discard(key)
            return result
        return wrapper
    
    return recursive_block

