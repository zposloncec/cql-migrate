# Copyright 2014 ATS Advanced Telematic Systems GmbH
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# System imports
import subprocess

# Library imports
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra import AlreadyExists, InvalidRequest
from cassandra.auth import PlainTextAuthProvider

# Application imports
from .split import CqlChunk, splitCql

# Return codes for the Executor.execute method (in addition to throwing CqlExecutionFailed)
RAN_OK = 0
NO_CHANGE = 1


# These messages imply that the command failed in a 'safe' way
known_messages = (
    ('Cannot add already existing column family', NO_CHANGE), # Duplicate create table
    ('because it conflicts with an existing column', NO_CHANGE), # Duplicate alter table
)

class CqlExecutionFailed(Exception):
    def __init__(self, msg):
        super(CqlExecutionFailed, self).__init__(msg)


class CassandraExecutor(object):
    """Execute CQL by calling the python-cassandra library"""
    def __init__(self, host, port, username, password,keyspace):
        print(host)
        print(port)
        print(username)
        print(password)
        print(keyspace)
        auth_provider = PlainTextAuthProvider(username=username,password=password)
        cluster = Cluster([host], port, auth_provider=auth_provider)
        self.session = cluster.connect()
        self.session.set_keyspace(keyspace)
    def execute_chunk(self, chunk):
        assert isinstance(chunk, CqlChunk)
        if chunk.is_comment():
            return NO_CHANGE
        if chunk.is_update():
            i = chunk.info
            query = "SELECT %s from %s WHERE %s=%s;" % (i.col, i.table, i.pkcol, i.pkvalue)
            res = self.select(query)
            if len(res) > 0 and res[0][0] != None:
                return NO_CHANGE
        return self.execute_raw(chunk.body())

    def execute_raw(self, cql):
        try:
            self.session.execute(cql)
            return RAN_OK
        except AlreadyExists:
            return NO_CHANGE
        except InvalidRequest, e:
            if 'code=2200' in str(e):
                return NO_CHANGE
            else:
                raise CqlExecutionFailed(str(e))
    def select(self, query):
        return self.session.execute(query)
# vim: set expandtab tabstop=4 shiftwidth=4:
