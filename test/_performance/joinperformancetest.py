## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from lxml.etree import XML

from meresco.xml import xpathFirst

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest


class JoinPerformanceTest(IntegrationTestCase): 
    def xxxtestJoin(self):
        #header, body = getRequest(port=self.solrPort, path='/solr/core1/select', arguments={'q': '*:* AND field1:value'}, parse=False)
        #body = XML(body)
        #t = qtime(body)
        t = 42
        print 'baseline (intersection within 1 core):', t

        header, body = getRequest(port=self.solrPort, path='/solr/core1/select', arguments={'q': '*:*', 'fq': ['{!join fromIndex=core2 from=__id__ to=__id__}*:*']}, parse=False)
        body = XML(body)
        t = qtime(body)
        #t = 63
        print '1 intersect over 2 cores:', t

        header, body = getRequest(port=self.solrPort, path='/solr/core1/select', arguments={'q': '*:*', 'fq': ['{!join fromIndex=core2 from=__id__ to=__id__}*:*', '{!join fromIndex=core3 from=__id__ to=__id__}*:*']}, parse=False)
        self.assertTrue('200 OK' in header, header + body)
        body = XML(body)
        t = qtime(body)
        print '2 interects over 3 cores:', t
        #self.assertTiming(200, t, 500)
        # self.assertEquals('477', xpathFirst(body, '//result/@numFound'))

    def testFacetJoin(self):
        def queryWithFacet(n):
            totalT = 0
            for i in xrange(0, n):
                header, body = getRequest(port=self.solrPort, path='/solr/core1/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!facetjoin core=core2 from=joinhash.__id__ to=joinhash.__id__}field2'}, timeOutInSeconds=30, parse=False)
                self.assertTrue('200 OK' in header, header + body)
                body = XML(body)
                totalT += int(qtime(body))
            print 'facet join over 2 cores (%sx):' % n, (totalT / n)
        queryWithFacet(1)
        queryWithFacet(3)
        queryWithFacet(25)
        queryWithFacet(100)

def qtime(body):
    return int(xpathFirst(body, '//int[@name="QTime"]/text()'))
