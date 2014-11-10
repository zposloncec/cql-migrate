#! /usr/bin/env python

import unittest
from unittest import TestCase
from os.path import join, dirname, normpath
from os import walk
import re

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


alter = """
alter table bar add bax text;
alter table bar add ggg text;
"""

alter_res = [ "alter table bar add bax text;", "alter table bar add ggg text;" ]


update = """
update tok set details='asdf' WHERE name='bob';
alter table bar add ggg text;
"""

update_res = [ "update tok set details='asdf' WHERE name='bob';", "alter table bar add ggg text;" ]


keyspace = """
CREATE KEYSPACE IF NOT EXISTS my_keyspace
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};
alter table bar add ggg text;
"""


class SplitCQL(TestCase):
    def testCreateSplit(self):
        res = cqlmigrate.splitCql(simple)
        body = [x.body() for x in res]
        self.assertEquals(body, simple_res)
        self.assertEquals([x.is_update() for x in res], [False, False])
    def testAlterSplit(self):
        res = cqlmigrate.splitCql(alter)
        body = [x.body() for x in res]
        self.assertEquals(body, alter_res)
        self.assertEquals([x.is_update() for x in res], [False, False])
    def testUpdate(self):
        res = cqlmigrate.splitCql(update)
        body = [x.body() for x in res]
        self.assertEquals(body, update_res)
        self.assertEquals([x.is_update() for x in res], [True, False])
        u = res[0].info
        self.assertEquals(u.table, 'tok')
        self.assertEquals(u.col, 'details')
        self.assertEquals(u.value ,'asdf')
        self.assertEquals(u.pkcol ,'name')
        self.assertEquals(u.pkvalue ,'bob')
    def testKeyspace(self):
        res = cqlmigrate.splitCql(keyspace)
        self.assertEquals(len(res), 2)


re_tab_nl = re.compile('[ \t]$', re.M)

class CodeStyle(TestCase):
    """Check some code style issues, specifically trailing whilespace and
    tabs rather than spaces """
    def _checkfile(self, root, name):
        if name.endswith('.py'):
            path = join(root, name)
            with open(path) as f:
                contents = f.read()
                self.assertFalse("\t" in contents, path + " contains a tab character")
                m = re_tab_nl.search(contents)
                lineno = -1
                if m:
                    lineno = len(contents[:m.start()].splitlines())
                    self.fail(path + " contains trailing whitespace on line %d" % lineno)
    def testNoTabs(self):
        projroot = normpath(join(dirname(__file__), '..'))
        for d in ['cqlmigrate', 'test']:
            for root, dirs, files in walk(join(projroot,d)):
                for name in files:
                    self._checkfile(root, name)

if __name__ == '__main__':
    unittest.main()
# vim: set expandtab tabstop=4 shiftwidth=4:
