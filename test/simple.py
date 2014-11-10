#! /usr/bin/env python

import unittest
from unittest import TestCase

import cqlmigrate

simple = """
CREATE TABLE IF NOT EXISTS auth_plus.clients (
  client_id uuid, -- A comment
  description text,
  PRIMARY KEY (client_id)
);

CREATE TABLE IF NOT EXISTS auth_plus.users (
  oemname text,
  username text,
  password text,
  PRIMARY KEY (oemname, username)
);
"""

simple_res = ["""CREATE TABLE IF NOT EXISTS auth_plus.clients (
  client_id uuid, -- A comment
  description text,
  PRIMARY KEY (client_id)
);""", """CREATE TABLE IF NOT EXISTS auth_plus.users (
  oemname text,
  username text,
  password text,
  PRIMARY KEY (oemname, username)
);"""]


class SplitCQL(TestCase):
    def testSimpleSplit(self):
        res = cqlmigrate.splitCql(simple)
        body = [x.body() for x in res]
        self.assertEquals(body, simple_res)
        self.assertEquals([i.is_create() for i in res], [True, True])

if __name__ == '__main__':
    unittest.main()

# vim: set expandtab tabstop=4 shiftwidth=4:
