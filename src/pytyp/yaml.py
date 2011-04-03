
try:
    from yaml import safe_dump, safe_dump_all, safe_load, safe_load_all

    from pytyp import encode, decode
    
    
    def dump(data, stream=None, **kargs):
        '''
        Serialize `obj` as a YAML formatted stream (or return a string).

        :param data: The Python object (or collection) to encode.
        :param stream: The destination for the data.
        :param kargs: Additional parameters are passed directly to the 
                      corresponding routine in pyyaml.

        Here is an example of encoding a Python class, and then reading that
        back from YAML:

          >>> class Example():
          ...     def __init__(self, foo):
          ...         self.foo = foo
          ...     def __repr__(self):
          ...         return '<Example({0})>'.format(self.foo)
          >>> dump(Example('abc'))
          '{foo: abc}\\n'
          >>> load = make_load(Example)
          >>> load('{foo: abc}')
          <Example(abc)>
        '''
        return safe_dump(encode(data), stream=stream, **kargs)
    
    
    def dump_all(data, stream=None, **kargs):
        '''
        Serialize a sequence of values as a YAML formatted stream (or return a
        string).

        :param data: A generators of Python values.
        :param stream: The destination for the data.
        :param kargs: Additional parameters are passed directly to the 
                      corresponding routine in pyyaml.

        Here is an example of encoding a series of Python classes, and then
        reading that back from YAML:

          >>> class Example():
          ...     def __init__(self, foo):
          ...         self.foo = foo
          ...     def __repr__(self):
          ...         return '<Example({0})>'.format(self.foo)
          >>> dump_all([Example('abc'), Example('xyz')])
          '{foo: abc}\\n--- {foo: xyz}\\n'
          >>> load_all = make_load_all([Example, Example])
          >>> list(load_all('{foo: abc}\\n--- {foo: xyz}\\n'))
          [<Example(abc)>, <Example(xyz)>]

        .. note::
        
          The `_all()` routines work with YAML's support for multiple
          documents.  Each document is handled separately and the list
          `[Example, Example]` above, as an argument to `make_load_all()`, is
          not a type specification, but an iterable collection of type
          specifications, one per document.
        '''
        return safe_dump_all((encode(d) for d in data), 
                             stream=stream, **kargs)
    
    
    def make_load(spec):
        '''
        Create a replacement for the `load()` function in pyyaml that will
        deserialize a stream containing a YAML document to a Python object.

        :param spec: The type specification for the root object.  Nested
                     objects are defined by type annotations.  See
                     :ref:`decoding` for full details.

        The documentation for `dump()` above contains an example of use.
        '''
        def load(stream, **kargs):
            return decode(spec, safe_load(stream, **kargs))
        return load
    
    
    def make_load_all(spec):
        '''
        Create a replacement for the `load_all()` function in pyyaml that will
        deserialize a stream containing multiple YAML documents to Python
        objects.

        :param spec: A generator giving type specifications for the root
                     objects.  Nested objects are defined by type annotations.
                     See :ref:`decoding` for full details.

        The documentation for `dump_all()` above contains an example of use.
        '''
        def load_all(stream, **kargs):
            for (s, d) in zip(spec, safe_load_all(stream, **kargs)):
                yield decode(s, d)
        return load_all

except ImportError:
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()

