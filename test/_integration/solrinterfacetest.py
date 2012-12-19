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
from seecr.test.utils import postRequest
from simplejson import dumps, loads
from time import sleep

class SolrInterfaceTest(IntegrationTestCase):
    def testAddQueryDelete(self):
        addKwargs=dict(
                identifier='record:testAddQueryDelete',
                data='''<doc>
    <field name="__id__">record:testAddQueryDelete</field>
    <field name="title">The title</field>
</doc>''',
            )
        header, body = postRequest(port=self.solrClientPort, path='/add', data=dumps(addKwargs), parse=False)
        self.assertEquals('', body)
        sleep(0.1)

        response = self.executeQuery(luceneQueryString='__id__:record\:testAddQueryDelete')
        self.assertEquals(1, response['total'])
        self.assertEquals(['record:testAddQueryDelete'], response['hits'])

        header, body = postRequest(port=self.solrClientPort, path='/delete', data=dumps(dict(identifier='record:testAddQueryDelete')), parse=False)
        self.assertEquals('', body)
        sleep(0.1)

        response = self.executeQuery(luceneQueryString='__id__:record\:testAddQueryDelete')
        self.assertEquals(0, response['total'])

    def testDatabase(self):
        response = self.executeQuery(luceneQueryString='*:*')
        self.assertEquals(69, response['total'])

    def testPivoting(self):
        response = self.executeQuery(luceneQueryString='*:*', facets=[
            [{'field': 'untokenized.rdf:type'}, {'field': 'untokenized.dc:date'}]            
        ])

    def executeQuery(self, **queryKwargs):
        header, body = postRequest(port=self.solrClientPort, path='/executeQuery', data=dumps(queryKwargs), parse=False)
        responseType, responseDict = body.split(': ', 1)
        self.assertEquals('SolrResponse', responseType)
        return loads(responseDict)
