

if __name__ == '__main__':
    import doctest
    from pytyp.spec.abcs import *
    from pytyp.spec.check import *
    from pytyp.spec.dispatch import overload
    from pytyp.s11n.json import *
    from abc import *
    class SomeClass: pass
    random_object = SomeClass()
    print(doctest.testfile('/home/andrew/projects/personal/pytyp/pytyp/pytyp.rst',
                           module_relative=False,globs=globals()))
    