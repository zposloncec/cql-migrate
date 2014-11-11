from pyparsing import alphanums, nums, lineEnd, ParseResults
from pyparsing import CaselessLiteral, Regex, Word, Forward, QuotedString
from pyparsing import nestedExpr, Optional, OneOrMore

comment = Regex('--[^\n]*') + lineEnd

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

literal_int = Word(nums)
literal << (literal_string | literal_int | literal_map )


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
update = (CaselessLiteral("UPDATE") + identifier + CaselessLiteral("SET") + identifier + '=' + literal +
        CaselessLiteral("WHERE") + identifier + '=' + literal + ';')

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

# CREATE KEYSPACE
create_keyspace = (CaselessLiteral("CREATE") + CaselessLiteral("KEYSPACE") + ifnotexists + identifier
        + CaselessLiteral("WITH") + identifier + '=' + literal_map + ';')

create_keyspace.setParseAction(ParseActionSimple('CREATE KEYSPACE'))

cql = OneOrMore(ctable | alter | update | create_keyspace)

cql.ignore(comment)
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

def splitCql(s):
    chunk_breaks = cql.parseString(s, parseAll=True)
    res = [CqlChunk(s, chunk_type, info, start, None) for chunk_type, info, start in chunk_breaks]
    for i in xrange(0,len(res)-1):
        res[i].end = res[i+1].start
    return res

# vim: set expandtab tabstop=4 shiftwidth=4:
