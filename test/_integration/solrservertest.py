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
        postRequest(port=self.solrPort, path='/solr/core2/update', data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>
  <field name="__id__">record:0001</field>
  <field name="field0">value</field>
  <field name="field1">value2</field>
</doc></add> 
""", contentType='text/xml')
        postRequest(port=self.solrPort, path='/solr/core3/update', data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>
  <field name="__id__">record:0001</field>
  <field name="field2">value3</field>
</doc></add> 
""", contentType='text/xml')
        sleep(2)
        header, body = getRequest(port=self.solrPort, path='/solr/records/join', arguments={'q': '*:*', 'join': '{!myjoin core=core2}*:*', 'facet': 'on', 'facet.field': '__id__', 'facet.mincount': 1, 'joinFacet.field': ['{!myjoin core=core2}field0', '{!myjoin core=core2}field1', '{!myjoin core=core3}field2']}, parse=True)
        print tostring(body, pretty_print=True)
        self.assertEquals(['record:0001'], xpath(body, '//result[@name="joinResponse"]/doc/str[@name="__id__"]/text()'))
        self.assertEquals('record:0001', xpathFirst(body, '//lst[@name="facet_fields"]/lst[@name="__id__"]/int/@name'))
        self.assertEquals('value', xpathFirst(body, '//lst[@name="join_facet_counts"]//lst[@name="field0"]/int/@name'))
        self.assertEquals('value2', xpathFirst(body, '//lst[@name="join_facet_counts"]//lst[@name="field1"]/int/@name'))
        self.assertEquals('value3', xpathFirst(body, '//lst[@name="join_facet_counts"]//lst[@name="field2"]/int/@name'))

