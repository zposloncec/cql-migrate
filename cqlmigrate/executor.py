import subprocess

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


def classify(out, err, returncode):
    if out == '' and err == '' and returncode == 0:
        return RAN_OK
    for substring, res in known_messages:
        if substring in err:
            return res
    if err != '':
        raise CqlExecutionFailed(err)
    if returncode != 0:
        raise CqlExecutionFailed("Non-Zero return code from cqlsh:%d" % returncode)
    raise CqlExecutionFailed(out + err)



class CqlshExecutor(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
    def execute(self, chunk):
        """Execute a chunk of CQL. returns one of RAN_OK ... UPDATED on
        success, and throw an exception if there was an unexpected failure"""
        proc = subprocess.Popen(['cqlsh', self.host, "%d" % self.port],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out,err) = proc.communicate(chunk)
        return classify(out,err, proc.returncode)

# vim: set expandtab tabstop=4 shiftwidth=4:
