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
    def setUp(self):
        IntegrationTestCase.setUp(self)
        self._adds = []

    def tearDown(self):
        for (core, fields) in self._adds:
            id = dict(fields)['__id__']
            self._removeFromCore(core, id)

    def testJoinHybridWithSolrJoinComponent(self):
        self.postToCore('core2', [('__id__', 'record:0001'), ('field0', 'value'), ('field1', 'value2')])
        self.postToCore('core2', [('__id__', 'record:0002'), ('field1', 'value3')])
        self.postToCore('core3', [('__id__', 'record:0001'), ('field2', 'value3')])

        sleepWheel(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={
                'q': '*:*',
                'fq': [
                    '{!join fromIndex=core2 from=__id__ to=__id__}*:*',
                    '{!join fromIndex=core3 from=__id__ to=__id__}__id__:record\:0001'],
                'facet': 'on',
                'facet.field': '__id__',
                'facet.mincount': 1,
                'joinFacet.field': [
                    '{!facetjoin core=core2}field0',
                    '{!facetjoin core=core2}field1',
                    '{!facetjoin core=core3}field2']
            }, parse=True)
        self.assertEquals(['record:0001'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))
        self.assertEquals('value', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/text()'))
        self.assertEquals('value2', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/text()'))
        self.assertEquals('value3', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/text()'))

    def testJoinWithUnknownCore(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!facetjoin core=core_unknown}field0'}, parse=False)
        self.assertTrue('400 Bad Request' in header, header + body)
        self.assertTrue('Cross-core join: no such core core_unknown' in body, body)

    def testFacetJoinWithoutJoinQuery(self):
        self.postToCore('core2', [('__id__', 'record:0001')])
        sleepWheel(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!facetjoin core=core2}__id__'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(10, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/text()'))

    def testQueryWithoutJoin(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(10, len(xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()')))

    def testDrilldownFieldAsInvalidQuery(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={'q': '*:*', 'facet': 'on', 'joinFacet.field': '{!facetjoin core=core2}field:value:other'}, parse=True)
        self.assertTrue('200 OK' in header, header + tostring(body))
        self.assertEquals(0, len(xpath(body, '//lst[@name="field:value:other"]/str')))

    def testFacetsWithJoinOnFromToFields(self):
        self.postToCore('core2', [('__id__', 'ignoredid:0001'), ('foreignid.ref', 'record:0001'), ('field0', 'value'), ('field1', 'value2')])
        self.postToCore('core2', [('__id__', 'ignoredid:0002'), ('foreignid.ref', 'record:0001'), ('field1', 'value2')])
        self.postToCore('core2', [('__id__', 'ignoredid:0003'), ('foreignid.ref', 'record:0001'), ('field1', 'value4')])

        self.postToCore('core2', [('__id__', 'ignoredid:0004'), ('foreignid.ref', 'record:0002'), ('field1', 'value3')])
        self.postToCore('core3', [('__id__', 'ignoredid:0005'), ('foreignid.otherref', 'record:0001'), ('field2', 'value3')])
        sleepWheel(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/select', arguments={
                'q': '*:*',
                'fq': [
                    '{!join fromIndex=core2 from=foreignid.ref to=__id__}*:*',
                    '{!join fromIndex=core3 from=foreignid.otherref to=__id__}foreignid.otherref:record\:0001'
                ],
                'facet': 'on',
                'facet.field': '__id__',
                'facet.mincount': 1,
                'joinFacet.field': [
                    '{!facetjoin core=core2 from=foreignid.ref to=__id__}field0',
                    '{!facetjoin core=core2 from=foreignid.ref to=__id__}field1',
                    '{!facetjoin core=core3 from=foreignid.otherref to=__id__}field2'
                ]
            }, parse=True)

        #print tostring(body, pretty_print=True)
        self.assertEquals(['record:0001'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))

        self.assertEquals(['value'], sorted(xpath(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/@name')))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int[@name="value"]/text()'))

        self.assertEquals(['value2', 'value4'], sorted(xpath(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/@name')))

        self.assertEquals('2', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int[@name="value2"]/text()'))

        self.assertEquals(['value3'], sorted(xpath(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/@name')))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int[@name="value3"]/text()'))


    def postToCore(self, core, fields):
        self._adds.append((core, fields))
        postRequest(port=self.solrPort,
            path='/solr/%s/update' % core,
            data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>%s</doc></add>""" % ''.join('<field name="%s">%s</field>' % (f, v) for f, v in fields),
            contentType='text/xml')

    def _removeFromCore(self, core, id):
        header, body = postRequest(port=self.solrPort,
            path='/solr/%s/update' % core,
            data="""<delete xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><id>%s</id></delete>""" % id,
            contentType='text/xml', parse=False)
