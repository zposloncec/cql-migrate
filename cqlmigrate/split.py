from pyparsing import alphanums, lineEnd, ParseResults
from pyparsing import CaselessLiteral, Regex, Word, Forward
from pyparsing import nestedExpr, Optional, OneOrMore

comment = Regex('--[^\n]*') + lineEnd

identifier = Word(alphanums + '_.')
colnamelist = Forward()
colnamelist << ((identifier + ',' + colnamelist) | identifier)

pkey = CaselessLiteral("PRIMARY") + CaselessLiteral("KEY") + nestedExpr(content=colnamelist)

cqltype = Word(alphanums + '_<>.')
coldefn = pkey | (identifier + cqltype)
coldefnlist = Forward()
coldefnlist << ((coldefn + ',' + coldefnlist) | coldefn )


ctable = (CaselessLiteral("CREATE") + CaselessLiteral("TABLE") +
          Optional(CaselessLiteral("IF") +
                             CaselessLiteral("NOT") + 
                             CaselessLiteral("EXISTS"))
          + identifier + 
          nestedExpr(content=coldefnlist)
          + ';'
          )


def parseAction(s, loc, tocs):
    return ParseResults([('CREATE', loc)])

ctable.setParseAction(parseAction)

cql = OneOrMore(ctable)

cql.ignore(comment)
cql.enablePackrat()
cql.parseWithTabs()


class CqlChunk(object):
    def __init__(self, src, start, end):
        self.src = src
        self.start = start
        self.end = end
    def body(self):
        return self.src[self.start:self.end].strip()
    def is_create(self):
        return True

def splitCql(s):
    chunk_breaks = cql.parseString(s, parseAll=True)
    res = [CqlChunk(s, start, None) for t,start in chunk_breaks]
    for i in xrange(0,len(res)-1):
        res[i].end = res[i+1].start
    return res

# vim: set expandtab tabstop=4 shiftwidth=4:
