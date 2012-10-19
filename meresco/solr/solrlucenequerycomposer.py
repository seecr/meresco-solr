## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Meresco Solr"
# 
# "Meresco Solr" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Solr" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Solr"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from cqlparser import CqlVisitor, UnsupportedCQL
from re import compile

prefixRegexp = compile(r'^([\w-]{2,})\*$') # pr*, prefix* ....

def _formatTerm(index, termString):
    if prefixRegexp.match(termString):
        termString = termString.lower()
    else:
        termString = '"%s"' % termString.replace('\\', r'\\').replace('"', r'\"')
    return '%s:%s' % (index, termString)

def _formatBoost(query, boost):
    return '%s^%.1f' % (query, boost) if boost != 1 else query

class Cql2LuceneQueryVisitor(CqlVisitor):

    def __init__(self, ast, unqualifiedTermFields):
        CqlVisitor.__init__(self, ast)
        self._unqualifiedTermFields = unqualifiedTermFields

    def visitSCOPED_CLAUSE(self, node):
        clause = CqlVisitor.visitSCOPED_CLAUSE(self, node)
        if len(clause) == 1:
            return clause[0]
        return "(%s)" % ' '.join(clause)
    
    def visitINDEX(self, node):
        results = CqlVisitor.visitINDEX(self, node)
        return results.replace(':', '\\:')

    def visitSEARCH_CLAUSE(self, node):
        # possible children:
        # CQL_QUERY
        # SEARCH_TERM
        # INDEX, RELATION, SEARCH_TERM
        firstChild = node.children[0].name
        results = CqlVisitor.visitSEARCH_CLAUSE(self, node)
        if firstChild == 'SEARCH_TERM':
            (unqualifiedRhs,) = results
            unqualifiedTermFields = [
                _formatBoost(_formatTerm(fieldname, unqualifiedRhs), boost) 
                    for fieldname, boost in self._unqualifiedTermFields
                ]
            if len(unqualifiedTermFields) == 1:
                return unqualifiedTermFields[0]
            return "(%s)" % ' OR '.join(unqualifiedTermFields)
        elif firstChild == 'INDEX':
            (index, (relation, boost), term) = results
            if relation in ['==', 'exact']:
                query = '%s:"%s"' % (index, term)
            elif relation == '=':
                query = _formatTerm(index, term)
            else:
                raise UnsupportedCQL("Only =, == and exact are supported.")
            return _formatBoost(query, boost)
        else:
            ((query,),) = results
            return query

    def visitRELATION(self, node):
        results = CqlVisitor.visitRELATION(self, node)
        if len(results) == 1:
            relation = results[0]
            boost = 1.0
        else:
            (relation, (modifier, comparitor, value)) = results
            boost = float(value)
        return relation, boost
 
class SolrLuceneQueryComposer(object):
    def __init__(self, unqualifiedTermFields):
        self._unqualifiedTermFields = unqualifiedTermFields

    def compose(self, ast):
        (result, ) = Cql2LuceneQueryVisitor(ast, self._unqualifiedTermFields).visit()
        return result
