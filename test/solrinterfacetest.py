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
from meresco.solr.solrinterface import SolrInterface

from cgi import parse_qs

class SolrInterfaceTest(TestCase):
    
    def setUp(self):
        TestCase.setUp(self)
        self._solrInterface = SolrInterface("localhost", 8888)

    def testAdd(self):
        sendData = []
        self._solrInterface._send = lambda path, text: sendData.append((path, text))
        list(self._solrInterface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self.assertEquals(2, len(sendData))
        self.assertEquals(('/solr/update', '<add><record><data>recordData</data></record></add>'), sendData[0])
        self.assertEquals(('/solr/update', '<commit/>'), sendData[1])

    def testDelete(self):
        sendData = []
        self._solrInterface._send = lambda path, text: sendData.append((path, text))
        list(self._solrInterface.delete("record&:1"))
        self.assertEquals(2, len(sendData))
        self.assertEquals(('/solr/update', '<delete><id>%s</id></delete>' % "record&amp;:1"), sendData[0])
        self.assertEquals(('/solr/update', '<commit expungeDeletes="true"/>'), sendData[1])

    def testExecuteQuery(self):
        total, hits, path = self.executeQuery("meresco.exists:true", start=0, stop=10, sortBy=None, sortDescending=False, response=RESPONSE) 
        self.assertQuery("/solr/select?q=meresco.exists%3Atrue&start=0&rows=10", path)
        self.assertEquals(3, total)
        self.assertEquals(['1','3','5'], hits)

    def testExecuteQueryWithStartStopAndSortKeys(self):
        total, hits, path = self.executeQuery("meresco.exists:true", start=5, stop=10, sortBy="field", sortDescending=True, response=RESPONSE)
        self.assertQuery("/solr/select?q=meresco.exists%3Atrue&start=5&rows=5&sort=field+desc", path)
        self.assertEquals(3, total)
        self.assertEquals(['1','3','5'], hits)

    def testExecuteQuerySortAscending(self):
        total, hits, path = self.executeQuery("meresco.exists:true", start=0, stop=10, sortBy="field", sortDescending=False, response=RESPONSE)
        self.assertQuery("/solr/select?q=meresco.exists%3Atrue&start=0&rows=10&sort=field+asc", path)
        self.assertEquals(3, total)
        self.assertEquals(['1','3','5'], hits)

    def testDrilldown(self):
        total, hits, drilldownData, path = self.executeQuery("meresco.exists:true", fieldnamesAndMaximums=[('__all__', 5, False)], response=RESPONSE % FACET_COUNTS)
        result = dict(drilldownData)
        self.assertQuery("/solr/select?q=meresco.exists%3Atrue&start=0&rows=10&facet=on&facet.field=__all__&f.__all__.facet.sort=index&f.__all__.facet.limit=5", path)
        self.assertEquals(3, total)
        self.assertEquals(['1', '3', '5'], hits)
        self.assertEquals(['__all__'], result.keys())
        self.assertEquals([("term_0", 1), ("term_1", 2)], list(result['__all__']))

    def executeQuery(self, query, response, **kwargs):
        readData = []
        def read(path):
            readData.append(path)
        self._solrInterface._read = read
        gen = self._solrInterface.executeQuery(luceneQueryString=query, **kwargs)
        gen.next()
        try:
            gen.send(response)
        except StopIteration, e:
            response = e.message
            if getattr(response, 'drilldownData', None) is not None:
                return response.total, response.hits, response.drilldownData, readData[0]
            return response.total, response.hits, readData[0]

    def assertQuery(self, query1, query2):
        path1, arguments1 = query1.split("?", 1)
        arguments1 = parse_qs(arguments1, keep_blank_values=True)
        path2, arguments2 = query2.split("?", 1)
        arguments2 = parse_qs(arguments2, keep_blank_values=True)
        self.assertEquals(path1, path2)
        self.assertEquals(arguments1, arguments2)

RESPONSE = """
<response>
    <lst name="responseHeader">
        <int name="status">0</int>
        <int name="QTime">1</int>
        <lst name="params">
            <str name="indent">on</str>
            <str name="start">0</str>
            <str name="q">meresco.exists:true</str>
            <str name="version">2.2</str>
            <str name="rows">10</str>
        </lst>
    </lst>
    <result name="response" numFound="3" start="0">
        <doc>
            <arr name="__id__">
                <str>1</str>
            </arr>
        </doc>
        <doc>
            <arr name="__id__">
                <str>3</str>
            </arr>
        </doc>
        <doc>
            <arr name="__id__">
                <str>5</str>
            </arr>
        </doc>
    </result>
    %s
</response>"""

FACET_COUNTS="""
<lst name="facet_counts">
    <lst name="facet_queries"/>
    <lst name="facet_fields">
        <lst name="__all__">
            <int name="term_0">1</int>
            <int name="term_1">2</int>
        </lst>
    </lst>
    <lst name="facet_dates"/>
    <lst name="facet_ranges"/>
</lst>"""
