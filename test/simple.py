#! /usr/bin/env python

from os import walk
from os.path import join, dirname, normpath
from time import sleep
from unittest import TestCase, expectedFailure

import re
import subprocess
import unittest

# DUT
from cqlmigrate import splitCql, CassandraExecutor, RAN_OK, NO_CHANGE

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
        res = splitCql(simple)
        body = [x.body() for x in res]
        self.assertEquals(body, simple_res)
        self.assertEquals([x.is_update() for x in res], [False, False])
    def testAlterSplit(self):
        res = splitCql(alter)
        body = [x.body() for x in res]
        self.assertEquals(body, alter_res)
        self.assertEquals([x.is_update() for x in res], [False, False])
    def testUpdate(self):
        res = splitCql(update)
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
        res = splitCql(keyspace)
        self.assertEquals(len(res), 2)

CASSANDRA_HOST = 'localhost'
CASSANDRA_PORT = 9042

class DataNotOverwritten(TestCase):
    def setUp(self):
        self.executor = CassandraExecutor(CASSANDRA_HOST, CASSANDRA_PORT)
        init = """
        CREATE KEYSPACE IF NOT EXISTS DataNotOverwritten
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};
        CREATE TABLE DataNotOverwritten.tt (pk text, v int, PRIMARY KEY (pk));
        """
        # Create a temp keyspace/table
        self.executor.execute('DROP KEYSPACE IF EXISTS DataNotOverwritten;')
        [self.executor.execute(i.body()) for i in splitCql(init)]
    def testAddColumn(self):
        e = self.executor
        # Load initial data
        e.execute("UPDATE DataNotOverwritten.tt SET v = 4050 WHERE pk='bob';")
        self.assertEquals(NO_CHANGE, e.execute("CREATE TABLE DataNotOverwritten.tt (pk text, v int, PRIMARY KEY (pk));"))
        self.assertEquals(RAN_OK, e.execute("ALTER TABLE DataNotOverwritten.tt ADD newcol text;"))
        # Can write to new column
        e.execute("UPDATE DataNotOverwritten.tt SET newcol = 'newdata' WHERE pk='bob';")
        # Trying to create the column again is a no-op
        self.assertEquals(NO_CHANGE, e.execute("ALTER TABLE DataNotOverwritten.tt ADD newcol text;"))
        # Both new and old data are present
        r = e.select("SELECT v, newcol from DataNotOverwritten.tt WHERE pk='bob';")
        self.assertEquals(4050, r[0].v)
        self.assertEquals('newdata', r[0].newcol)

    @expectedFailure
    def testStaticSamePk(self):
        e = self.executor
        # The first time through the static data should be written
        e.execute("UPDATE DataNotOverwritten.tt SET v = 4050 WHERE pk='bob';")
        self.assertEquals(4050, e.select("SELECT v from DataNotOverwritten.tt WHERE pk='bob';")[0].v)
        # If data already exists for that primary key, the data shouldn't be written
        e.execute("UPDATE DataNotOverwritten.tt SET v = 4051 WHERE pk='bob';")
        self.assertEquals(4050, e.select("SELECT v from DataNotOverwritten.tt WHERE pk='bob';")[0].v)



re_tab_nl = re.compile('[ \t]$', re.M)

class CodeStyle(TestCase):
    """Check some code style issues, specifically trailing whilespace and
    tabs rather than spaces """
    def _checkpythonfile(self, root, name):
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
                    if name.endswith('.py'):
                        self._checkpythonfile(root, name)
        self._checkpythonfile(join(projroot,'bin'), 'cql-migrate')

if __name__ == '__main__':
    try:
        with open('hosts.conf') as f:
            content = f.read()
            host = re.search('cassandra.contact-points.0.host="([0-9.]+)"', content)
            CASSANDRA_HOST = host.group(1)
            port = re.search('cassandra.contact-points.0.port=([0-9]+)', content)
            CASSANDRA_PORT = int(port.group(1))
    except IOError:
        print "hosts.conf not found"
        pass
    print "Will connect to cassandra on %s:%d" % (CASSANDRA_HOST, CASSANDRA_PORT)
    unittest.main()
# vim: set expandtab tabstop=4 shiftwidth=4:
