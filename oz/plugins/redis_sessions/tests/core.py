from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz.plugins.redis_sessions
import oz
import unittest

@oz.test
class CDNCoreTest(unittest.TestCase):
    def test_password_hash(self):
        hash = oz.plugins.redis_sessions.password_hash("bar", password_salt="foo")
        self.assertEqual(hash, "sha256!c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2")

    def test_random_hex(self):
        hexchars = set("0123456789abcdef")

        s1 = oz.plugins.redis_sessions.random_hex(10)
        self.assertEqual(len(s1), 10)

        for c in s1:
            self.assertIn(c, hexchars)

        s2 = oz.plugins.redis_sessions.random_hex(10)
        self.assertEqual(len(s2), 10)

        for c in s2:
            self.assertIn(c, hexchars)

        self.assertNotEqual(s1, s2)
