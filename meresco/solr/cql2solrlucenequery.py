## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2013 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.core import Observable

from meresco.components.statistics import Logger
from meresco.components.clausecollector import ClauseCollector
from meresco.solr.solrlucenequerycomposer import SolrLuceneQueryComposer


class Cql2SolrLuceneQuery(Observable, Logger):
    def __init__(self, unqualifiedFields, name=None):
        Observable.__init__(self, name=name)
        self._cqlComposer = SolrLuceneQueryComposer(unqualifiedFields)

    def executeQuery(self, cqlAbstractSyntaxTree, *args, **kwargs):
        filterQueries = kwargs.get('filterQueries', [])
        filterQueries = [self._convert(fq) for fq in filterQueries]
        response = yield self.any.executeQuery(luceneQueryString=self._convert(cqlAbstractSyntaxTree), *args, **kwargs)
        raise StopIteration(response)

    def _convert(self, ast):
        ClauseCollector(ast, self.log).visit()
        return self._cqlComposer.compose(ast)

CQL2SolrLuceneQuery = Cql2SolrLuceneQuery
