from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz.redis_sessions
import oz
import unittest

@oz.test
class CDNCoreTestCase(unittest.TestCase):
    def test_password_hash(self):
        hash = oz.redis_sessions.password_hash("bar", password_salt="foo")
        self.assertEqual(hash, "sha256!c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2")

    def test_random_hex(self):
        hexchars = set("0123456789abcdef")

        s1 = oz.redis_sessions.random_hex(10)
        self.assertEqual(len(s1), 10)

        for c in s1:
            self.assertTrue(c in hexchars, "%s not in %s" % (c, hexchars))

        s2 = oz.redis_sessions.random_hex(10)
        self.assertEqual(len(s2), 10)

        for c in s2:
            self.assertTrue(c in hexchars, "%s not in %s" % (c, hexchars))

        self.assertNotEqual(s1, s2)
