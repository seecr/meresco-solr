## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import IntegrationTestCase

from seecr.test.utils import sleepWheel, getRequest, postRequest
from lxml.etree import XML, tostring
from meresco.xml import xpath, xpathFirst

class SolrJoinTest(IntegrationTestCase):

    def testJoinHybridWithSolrJoinComponent(self):
        postToCore(self.solrPort, 'core2', [('__id__', 'record:0001'), ('field0', 'value'), ('field1', 'value2')])
        postToCore(self.solrPort, 'core2', [('__id__', 'record:0002'), ('field1', 'value3')])
        postToCore(self.solrPort, 'core3', [('__id__', 'record:0001'), ('field2', 'value3')])
        sleepWheel(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'fq': ['{!join fromIndex=core2 from=__id__ to=__id__}*:*', '{!join fromIndex=core3 from=__id__ to=__id__}__id__:record\:0001'], 'facet': 'on', 'facet.field': '__id__', 'facet.mincount': 1, 'joinFacet.field': ['{!myjoin core=core2}field0', '{!myjoin core=core2}field1', '{!myjoin core=core3}field2']}, parse=True)
        self.assertEquals(['record:0001'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))
        self.assertEquals('value', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/text()'))
        self.assertEquals('value2', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/text()'))
        self.assertEquals('value3', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/text()'))

    def testJoinWithUnknownCore(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!myjoin core=core_unknown}field0'}, parse=False)
        self.assertTrue('400 Bad Request' in header, header + body)
        self.assertTrue('Cross-core join: no such core core_unknown' in body, body)

    def testFacetJoinWithoutJoinQuery(self):
        postToCore(self.solrPort, 'core2', [('__id__', 'record:0001')])
        sleepWheel(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!myjoin core=core2}__id__'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(10, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/text()'))

    def testQueryWithoutJoin(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(10, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))

    def testDrilldownFieldAsInvalidQuery(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!myjoin core=core2}field:value:other'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(0, len(xpath(body, '//lst[@name="field:value:other"]/str')))

    # def testJoinScore(self):
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0001')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0019')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0025')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0037')])
    #     sleepWheel(2)
    #     header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '__all__:history', 'fl': '*,score'}, parse=True)
    #     self.assertEquals(['record:0001', 'record:0019', 'record:0037', 'record:0025'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
    #     self.assertEquals(['0.7928962', '0.67962533', '0.56635445', '0.45308354'], xpath(body, '//result[@name="response"]/doc/float[@name="score"]/text()'))

    #     header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '__all__:history', 'fl': '*,score', 'join': '{!myjoin core=core2}*:*'}, parse=True)
    #     print tostring(body)
    #     self.assertEquals(['record:0001', 'record:0019', 'record:0037', 'record:0025'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
    #     self.assertEquals(['0.7928962', '0.67962533', '0.56635445', '0.45308354'], xpath(body, '//result[@name="response"]/doc/float[@name="score"]/text()'))

    # def testJoinResultList(self):
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0001')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0019')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0025')])
    #     postToCore(self.solrPort, 'core2', [('__id__', 'record:0037')])
    #     sleepWheel(2)
    #     header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '__all__:history', 'fl': '*,score', 'rows': '1'}, parse=True)
    #     self.assertEquals(1, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))

    #     header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '__all__:history', 'fl': '*,score', 'rows': '1', 'join': '{!myjoin core=core2}*:*'}, parse=True)
    #     self.assertEquals(1, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))

def postToCore(port, core, fields):
    postRequest(port=port, 
        path='/solr/%s/update' % core, 
        data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>%s</doc></add>""" % ''.join('<field name="%s">%s</field>' % (f, v) for f, v in fields),
        contentType='text/xml')

