Pytyp uses ABCs and function annotations in a consistent, pythonic way that supports declarative APIs - instead of saying how to do something, you have the ability to say what you want.

Full documentation and install instructions at http://www.acooke.org/pytyp/

Pytyp includes:

  * A basic set of type specifications for describing collections of data, closely integrated into the language:
```
    >>> isinstance([1,2,None,4], Seq(Opt(int)))
    True
```
  * A decorator that type-checks functions::
```
    >>> def str_only(x:str): return 'foo'
    >>> str_only(42)
    Exception raised:
      ...
    TypeError: Type str inconsistent with 42.
```
  * A decorator that allows dynamic dispatch by type.  You can combine multiple methods under one name, and then select which method is called by the type of an argument (normal OO programming uses the type of ```self``` to select the method; this is more like Lisp's multimethods).

  * Routines for converting between Python classes and JSON or YAML.  Instead of having to work with ```dict``` and ``list`` you can read JSON directly into Python classes.  This is included as an example of the declarative API possible - you describe the form of the output using type specifications.

The ideas behind the library are described in more dehtail in `Algebraic ABCs http://www.acooke.org/pytyp.pdf