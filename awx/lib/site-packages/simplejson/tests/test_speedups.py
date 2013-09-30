from unittest import TestCase

from simplejson import encoder, scanner

def has_speedups():
    return encoder.c_make_encoder is not None

class TestDecode(TestCase):
    def test_make_scanner(self):
        if not has_speedups():
            return
        self.assertRaises(AttributeError, scanner.c_make_scanner, 1)

    def test_make_encoder(self):
        if not has_speedups():
            return
        self.assertRaises(TypeError, encoder.c_make_encoder,
            None,
            "\xCD\x7D\x3D\x4E\x12\x4C\xF9\x79\xD7\x52\xBA\x82\xF2\x27\x4A\x7D\xA0\xCA\x75",
            None)
