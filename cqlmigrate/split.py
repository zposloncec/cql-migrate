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


from pyparsing import alphanums, nums, lineEnd, ParseResults
from pyparsing import CaselessLiteral, Regex, Word, Forward, QuotedString
from pyparsing import nestedExpr, Optional, OneOrMore


def itemlist(start, body, delimiter, end):
    a = Forward()
    a << ((body + delimiter + a) | body)
    return nestedExpr(opener=start, closer=end, content=a, ignoreExpr=None)

identifier = Word(alphanums + '_.')

pkey = CaselessLiteral("PRIMARY") + CaselessLiteral("KEY") + itemlist('(', identifier, ',', ')')

cqltype = Word(alphanums + '_<>.')
coldefn = pkey | (identifier + cqltype)

ifnotexists = Optional(CaselessLiteral("IF") + CaselessLiteral("NOT") + CaselessLiteral("EXISTS"))

literal = Forward()
literal_string = QuotedString("'", unquoteResults=False)

map_kv = literal_string + ':' + literal
literal_map = itemlist('{', map_kv, ',', '}')

literal_set = itemlist('{', literal, ',', '}')
# Matches numbers and uuids
literal_int_uuid = Word('0123456789abcdefABCEDEF-.')

literal << (literal_string | literal_int_uuid | literal_set | literal_map)


class ParseActionSimple(object):
    def __init__(self, tagas):
        self.tagas = tagas
    def __call__(self, s, loc, tocs):
        return ParseResults([(self.tagas, None, loc)])

# CREATE TABLE ...
ctable = (CaselessLiteral("CREATE") + CaselessLiteral("TABLE") + ifnotexists
          + identifier + itemlist('(', coldefn, ',', ')') + ';')

ctable.setParseAction(ParseActionSimple('CREATE'))

# ALTER TABLE ....
alter = (CaselessLiteral("ALTER") + CaselessLiteral("TABLE") + identifier + CaselessLiteral("ADD") +
        identifier + cqltype + ";")

alter.setParseAction(ParseActionSimple('ALTER'))


# UPDATE ....
update_where = Forward()
update_constraint = identifier + '=' + literal;
update_where << ((update_constraint + "AND" + update_where) | update_constraint)

update = (CaselessLiteral("UPDATE") + identifier + CaselessLiteral("SET") + identifier + '=' + literal +
        CaselessLiteral("WHERE") + update_where + ';')

class UpdateStatement(object):
    """Information about the an UPDATE statement. Note that pkvalue and value
    are stored as strings that are suitable literals for CQL, so the string "fred" is
    stored as "'fred'" and the integer 123 is stored as "123"."""
    def __init__(self, table, pkcol, pkvalue, col, value):
        self.table = table
        self.pkcol = pkcol
        self.pkvalue = pkvalue
        self.col = col
        self.value = value
    def __str__(self):
        return "UPDATE table:%s pkey:%s=%s col:%s value:%s" % (self.table, self.pkcol, self.pkvalue, self.col, self.value)

def updateParseAction(s, loc, tocs):
    info = UpdateStatement(tocs[1], tocs[7], tocs[9], tocs[3], tocs[5])
    return ParseResults([('UPDATE', info, loc)])

update.setParseAction(updateParseAction)

# INSERT
insert = (CaselessLiteral("INSERT") + CaselessLiteral("INTO") + identifier + itemlist('(', identifier, ',', ')') +
        CaselessLiteral("VALUES") + itemlist('(', literal, ',', ')') + ';')

insert.setParseAction(ParseActionSimple('INSERT'))

# CREATE KEYSPACE
create_keyspace = (CaselessLiteral("CREATE") + CaselessLiteral("KEYSPACE") + ifnotexists + identifier
        + CaselessLiteral("WITH") + identifier + '=' + literal_map + ';')

create_keyspace.setParseAction(ParseActionSimple('CREATE KEYSPACE'))

# Comments
# It would be nice to remove comments in the lexing stage, except that
# they are not part of the language that cassandra understands: they are
# part of cqlsh. Instead mark them as special chunks and skip them in
# the executor. This means that comments may only appear between
# statements.
comment = Regex('(--|//)[^\n]*') + lineEnd

comment.setParseAction(ParseActionSimple('COMMENT'))

cql = OneOrMore(ctable | alter | update | insert | create_keyspace | comment)

cql.enablePackrat()
cql.parseWithTabs()


class CqlChunk(object):
    def __init__(self, src, chunk_type, info, start, end):
        self.src = src
        self.chunk_type = chunk_type
        self.info = info
        self.start = start
        self.end = end
    def body(self):
        return self.src[self.start:self.end].strip()
    def is_update(self):
        return self.chunk_type == 'UPDATE'
    def is_comment(self):
        return self.chunk_type == 'COMMENT'

def splitCql(s):
    chunk_breaks = cql.parseString(s, parseAll=True)
    res = [CqlChunk(s, chunk_type, info, start, None) for chunk_type, info, start in chunk_breaks]
    for i in xrange(0,len(res)-1):
        res[i].end = res[i+1].start
    return res

# vim: set expandtab tabstop=4 shiftwidth=4:
