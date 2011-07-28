## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase
from cq2utils import CallTrace
from cqlparser import parseString
from meresco.solr.cql2solrlucenequery import CQL2SolrLuceneQuery
from meresco.core import be, Observable

class CQL2SolrLuceneQueryTest(TestCase):
    def setUp(self):
        self.convertor = CQL2SolrLuceneQuery([('field', 1.0)])
        self.observer = CallTrace('Query responder')
        self.dna = be((Observable(),
            (self.convertor, 
                (self.observer,),
            )
        ))
        self.loggedClauses = []
        def logShunt(clause, **kwargs):
            self.loggedClauses.append(clause)
        self.convertor.log = logShunt

    def assertLog(self, expectedClauses, query):
        self.loggedClauses = []
        list(self.dna.any.executeQuery(cqlAbstractSyntaxTree=parseString(query)))
        self.assertEquals(expectedClauses, self.loggedClauses)

    def testOneTerm(self):
        self.assertLog(['term'], 'term')
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals("executeQuery", self.observer.calledMethods[0].name)
        self.assertEquals("field:term", self.observer.calledMethods[0].kwargs['luceneQueryString'])

    def testIndexRelationTerm(self):
        self.assertLog(['field = term'], 'field=term')

    def testIndexRelationBoostTerm(self):
        self.assertLog(['field =/boost=1.1 term'], "field =/boost=1.1 term")

    def testIndexExactTerm(self):
        self.assertLog(['field exact term'], 'field exact term')
        self.assertLog(['field exact "term with spaces"'], 'field exact "term with spaces"')

    def testTermAndTerm(self):
        self.assertLog(['term1', 'term2'], 'term1 AND term2')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 AND term2 OR term3')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 AND (term2 OR term3)')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 OR term2 AND term3')

    def testBraces(self):
        self.assertLog(['term'], '(term)')

