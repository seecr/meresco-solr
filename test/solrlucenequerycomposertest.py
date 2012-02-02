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

from cq2utils import CQ2TestCase

from cqlparser import parseString, UnsupportedCQL
from meresco.solr.solrlucenequerycomposer import SolrLuceneQueryComposer

class SolrLuceneQueryComposerTest(CQ2TestCase):
    def testOne(self):
        printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 1.0)])
        ast = parseString("term")
        self.assertEquals('__all__:term', printer.compose(ast))
        ast = parseString("fiets AND auto")
        self.assertEquals('__all__:fiets AND __all__:auto', printer.compose(ast))
        ast = parseString('"fiets auto"')
        self.assertEquals('__all__:"fiets auto"', printer.compose(ast))
        ast = parseString('"fi*"')
        self.assertEquals('__all__:fi*', printer.compose(ast))
        ast = parseString('fi*')
        self.assertEquals('__all__:fi*', printer.compose(ast))

    def testEscaping(self):
        printer = SolrLuceneQueryComposer(unqualifiedTermFields=[])
        ast = parseString('field="term:term1"')
        self.assertEquals('field:"term:term1"', printer.compose(ast))
        ast = parseString('field exact "term:term1"')
        self.assertEquals('field:"term:term1"', printer.compose(ast))
        ast = parseString('field exact term')
        self.assertEquals('field:"term"', printer.compose(ast))
        ast = parseString('dc:title exact term')
        self.assertEquals(r'dc\:title:"term"', printer.compose(ast))

    def testMultipleUnqualifiedTermFields(self):
        printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 1.0), ("__extra__", 1.0)])
        ast = parseString("term")
        self.assertEquals('__all__:term OR __extra__:term', printer.compose(ast))

    def testBoost(self):
        printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 4.0)])
        ast = parseString("term")
        self.assertEquals('__all__:term^4.0', printer.compose(ast))

        ast = parseString("field=/boost=3.5 term")
        self.assertEquals('field:term^3.5', printer.compose(ast))

        printer = SolrLuceneQueryComposer(unqualifiedTermFields=[("__all__", 4.0), ("__extra__", 2.0), ("__uri__", 1.0)])
        ast = parseString("term")
        self.assertEquals('__all__:term^4.0 OR __extra__:term^2.0 OR __uri__:term', printer.compose(ast))

        printer=SolrLuceneQueryComposer(unqualifiedTermFields=[("all", 1)])
        ast = parseString("field exact/boost=2 term")
        self.assertEquals('field:"term"^2.0', printer.compose(ast))

    def testUnsupportedCQL(self):
        printer=SolrLuceneQueryComposer(unqualifiedTermFields=[("all", 1)])
        ast = parseString("field > term")
        try:
            printer.compose(ast)
            self.fail("must raise UnsupportedCQL")
        except UnsupportedCQL, e:
            self.assertEquals("%s only supports =, == and exact." % SolrLuceneQueryComposer.__name__, str(e))

