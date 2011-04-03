
from unittest import TestCase

from pytyp import encode, decode
from pytyp._test.support import SimpleArgs, NamedArgs, ArgsAndKArgs,\
    MissingKArgs, TypedKArgs


class RoundtripTest(TestCase):
    
    def assert_roundtrip(self, spec, obj, target=None, strict=True):
        target = target or obj
        result = decode(spec, encode(obj, strict=strict))
        assert result == target, result
    
    def test_tuple(self):
        self.assert_roundtrip((SimpleArgs, NamedArgs),
                              (SimpleArgs(1,2,3), NamedArgs(1,2)))

    def test_args_and_kargs(self):
        self.assert_roundtrip(ArgsAndKArgs,
                              ArgsAndKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
                                           foo=7, bar=8))

    def test_missing_kargs(self):
        try:
            self.assert_roundtrip(MissingKArgs,
                                  MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
                                               foo=7, bar=NamedArgs(8,9)))
            assert False, 'Expected error'
        except AttributeError:
            pass
        try:
            self.assert_roundtrip(MissingKArgs,
                                  MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
                                               foo=7, bar=8),
                                  strict=False)
            assert False, 'Eexpected error'
        except AssertionError:
            pass
        # here we don't have an exact match because we used non-strict matching,
        # which allowed for missing kargs
        self.assert_roundtrip(MissingKArgs,
                              MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6),
                                           foo=7, bar=8),
                              target=MissingKArgs(SimpleArgs(1,2,3), SimpleArgs(4,5,6)),
                              strict=False)
        
    def test_typed_kargs(self):
        self.assert_roundtrip(TypedKArgs, TypedKArgs(foo=SimpleArgs(1,2,3)))
