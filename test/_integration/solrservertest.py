## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from seecr.test.utils import getRequest, postRequest
from time import sleep
from meresco.xml import xpathFirst, xpath
from lxml.etree import tostring

class SolrServerTest(IntegrationTestCase): 
    def testAdminPingInterface(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/admin/ping', parse=True)
        self.assertEquals(['OK'], body.xpath('/response/str[@name="status"]/text()'))

    def testAdminInterface(self):
        header, body = getRequest(port=self.solrPort, path='/solr/#', parse=False)
        self.assertTrue('<title>Solr Admin</title>' in body, body)

    def testJoin(self):
        postToCore(self.solrPort, 'core2', [('__id__', 'record:0001'), ('field0', 'value'), ('field1', 'value2')])
        postToCore(self.solrPort, 'core2', [('__id__', 'record:0002'), ('field1', 'value3')])
        postToCore(self.solrPort, 'core3', [('__id__', 'record:0001'), ('field2', 'value3')])
        sleep(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/join', arguments={'q': '*:*', 'join': ['{!myjoin core=core2}*:*', '{!myjoin core=core3}__id__:record\:0001'], 'facet': 'on', 'facet.field': '__id__', 'facet.mincount': 1, 'joinFacet.field': ['{!myjoin core=core2}field0', '{!myjoin core=core2}field1', '{!myjoin core=core3}field2']}, parse=True)
        print tostring(body, pretty_print=True)
        self.assertEquals(['record:0001'], xpath(body, '//result[@name="response"]/doc/str[@name="__id__"]/text()'))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="__id__"]/int/@name'))
        self.assertEquals('value', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field0"]/int/text()'))
        self.assertEquals('value2', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field1"]/int/text()'))
        self.assertEquals('value3', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/@name'))
        self.assertEquals('1', xpathFirst(body, '//lst[@name="facet_counts"]//lst[@name="field2"]/int/text()'))

def postToCore(port, core, fields):
    postRequest(port=port, 
        path='/solr/%s/update' % core, 
        data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>%s</doc></add>""" % ''.join('<field name="%s">%s</field>' % (f, v) for f, v in fields),
        contentType='text/xml')

