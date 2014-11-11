# System imports
import subprocess

# Library imports
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra import AlreadyExists, InvalidRequest

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
    def __init__(self, host, port):
        cluster = Cluster([host], port)
        self.session = cluster.connect()
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
