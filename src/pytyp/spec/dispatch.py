#LICENCE

from collections import OrderedDict
from functools import wraps
from inspect import getcallargs

from pytyp.spec.check import unpack, verify_all


class DispatchError(TypeError): pass


class Overload:
    '''
    This class implements the ``overload`` decorator via the constructor.  It
    implements a data descriptor that returns the wrapper method (and the
    ``.intercept()`` method, used to add additional methods).
    '''
    
    def __init__(self, default):
        self.__name__ = default.__name__
        if unpack(default)[0]:
            raise DispatchError('Default method {} has type specifications.'
                                .format(default.__name__))
        self._final = None
        self.intercept(default)
        
    def intercept(self, method):
        self._final = self.wrap(method, self._final)
        return self._final
    
    def __get__(self, obj, objtype=None):
        if obj:
            return lambda *args, **kargs: self._final(obj, *args, **kargs)
        else:
            return self
    
    @staticmethod
    def wrap(method, previous):
        annotation = unpack(method)[0]
        @wraps(method)
        def wrapper(obj, *args, **kargs):
            callargs = getcallargs(method, obj, *args, **kargs)
            try:
                verify_all(callargs, annotation)
            except TypeError:
                #print('Failed {} with {} {}'.format(method.__name__, args, kargs))
                if previous:
                    return previous(obj, *args, **kargs)
                else:
                    raise
            wrapper.obj = obj # for previous
            return method(obj, *args, **kargs)
        wrapper.previous = lambda *args, **kargs: previous(wrapper.obj, *args, **kargs)
        return wrapper
    
overload = Overload
'''
This is the decorator for dynamic dispatch by type.  It should be placed on the
default method - it is that method whose name will be called for *all* the 
overloaded methods.

Additional methods are then marked by a decorator that is ``.intercept`` on the
default.  For example::

  class MyClass:
  
      @overload
      def default_method(self, foo, bar):
          # code here runs if foo is not a sequence (or list)
          
      @default_method.intercept
      def foo_seq(self, foo:Sequence, bar):
          # code here runs if foo is a sequence (but not a string!)

      @default_method.intercept
      def foo_list(self, foo:list, bar):
          # code here runs if foo is a list
          
In the example above, when ``default_method()`` is called, any of the three 
methods might be used, depending on the type of ``foo``.

The order in which methods are checked is "bottom to top" and a method can 
pass the call "up" by calling ``.previous()`` on itself.  So, for example, 
code in ``foo_list()`` can call ``foo_seq()`` via ``self.foo_list.previous()``.
'''
