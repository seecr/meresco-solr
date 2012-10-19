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

from seecr.test import SeecrTestCase

from cqlparser import parseString, UnsupportedCQL
from meresco.solr.solrlucenequerycomposer import SolrLuceneQueryComposer

class SolrLuceneQueryComposerTest(SeecrTestCase):
    def testOne(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 1.0)])
        self.assertEquals('__all__:"term"', self.cql2lucene("term"))
        self.assertEquals('(__all__:"fiets" AND __all__:"auto")', self.cql2lucene("fiets AND auto"))
        self.assertEquals('__all__:"fiets auto"', self.cql2lucene('"fiets auto"'))
        self.assertEquals('__all__:fi*', self.cql2lucene('"fi*"'))
        self.assertEquals('__all__:fi*', self.cql2lucene('fi*'))
        self.assertEquals('__all__:f*ts', self.cql2lucene('"f*ts"'))
        self.assertEquals('__all__:*ts', self.cql2lucene('*ts'))
        self.assertEquals('(__all__:"fiets" AND (__all__:"auto" OR __all__:"boot"))', self.cql2lucene('fiets AND (auto OR boot)'))
        self.assertEquals('((__all__:"fiets" AND __all__:"auto") OR __all__:"boot")', self.cql2lucene('fiets AND auto OR boot'))
        self.assertEquals('(__all__:"fiets" AND (__all__:"auto" OR __all__:"boot"))', self.cql2lucene('fiets AND (auto OR boot)'))
        self.assertEquals('((__all__:"fiets" AND __all__:"auto") OR (__all__:"boot" AND __all__:"other"))', self.cql2lucene('(fiets AND auto) OR (boot AND other)'))
        self.assertEquals('(__all__:"fiets" OR (__all__:"auto" AND __all__:"boot"))', self.cql2lucene('fiets OR auto AND boot'))

    def testEscaping(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[])
        self.assertEquals('field:"term:term1"', self.cql2lucene('field="term:term1"'))
        self.assertEquals('field:"term:term1"', self.cql2lucene('field exact "term:term1"'))
        self.assertEquals('field:"term"', self.cql2lucene('field exact term'))
        self.assertEquals(r'dc\:title:"term"', self.cql2lucene('dc:title exact term'))

    def testSolrKeywords(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[])
        self.assertEquals('field:"NOT"', self.cql2lucene('field="NOT"'))
        self.assertEquals('field:"AND"', self.cql2lucene('field="AND"'))
        self.assertEquals('field:"OR"', self.cql2lucene('field="OR"'))
        # Escaping Special Characters
        # Lucene supports escaping special characters that are part of the query syntax. The current list special characters are
        # + - && || ! ( ) { } [ ] ^ " ~ * ? : \
        # To escape these character use the \ before the character.
        self.assertEquals('field:"-"', self.cql2lucene('field=-'))
        self.assertEquals('field:"+"', self.cql2lucene('field=+'))
        self.assertEquals('field:"!"', self.cql2lucene('field="!"'))
        self.assertEquals('field:"!"', self.cql2lucene('field=!'))
        self.assertEquals('field:"&&"', self.cql2lucene('field="&&"'))
        self.assertEquals(r'field:"\""', self.cql2lucene(r'field="\""'))
        self.assertEquals(r'field:"fiets!"', self.cql2lucene(r'field="fiets!"'))
        self.assertEquals(r'field:"fiets!"', self.cql2lucene(r'field=fiets!'))

    def testPrefixQuery(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 1.0)])
        self.assertEquals('__all__:term*', self.cql2lucene('term*'))
        self.assertEquals('__all__:term*', self.cql2lucene('TERM*'))

    def testMultipleUnqualifiedTermFields(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 1.0), ("__extra__", 1.0)])
        self.assertEquals('(__all__:"term" OR __extra__:"term")', self.cql2lucene("term"))
        self.assertEquals('((__all__:"term" OR __extra__:"term") AND (__all__:"otherterm" OR __extra__:"otherterm"))', self.cql2lucene("term AND otherterm"))

    def testBoost(self):
        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 4.0)])
        self.assertEquals('__all__:"term"^4.0', self.cql2lucene("term"))

        self.assertEquals('field:"term"^3.5', self.cql2lucene("field=/boost=3.5 term"))

        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 4.0), ("__extra__", 2.0), ("__uri__", 1.0)])
        self.assertEquals('(__all__:"term"^4.0 OR __extra__:"term"^2.0 OR __uri__:"term")', self.cql2lucene("term"))

        self.printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("all", 1)])
        self.assertEquals('field:"term"^2.0', self.cql2lucene("field exact/boost=2 term"))

    def testUnsupportedCQL(self):
        printer=SolrLuceneQueryComposer(unqualifiedTermFields=[("all", 1)])
        ast = parseString("field > term")
        try:
            printer.compose(ast)
            self.fail("must raise UnsupportedCQL")
        except UnsupportedCQL, e:
            self.assertEquals("Only =, == and exact are supported.", str(e))

    def cql2lucene(self, cql):
        return self.printer.compose(parseString(cql))
