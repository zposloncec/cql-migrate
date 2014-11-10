#! /usr/bin/env python

import unittest
from unittest import TestCase

class Dummy(TestCase):
    def testJenkins(self):
        self.assertEquals(1,1, "CI works")

if __name__ == '__main__':
    unittest.main()

# vim: set expandtab tabstop=4 shiftwidth=4:
