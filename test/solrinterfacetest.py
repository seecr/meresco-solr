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

from unittest import TestCase

from cgi import parse_qs

from weightless.core import compose
from weightless.io import Suspend
from meresco.core import Observable
from meresco.solr.solrinterface import SolrInterface
from seecr.test import CallTrace


class SolrInterfaceTest(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self._solrInterface = SolrInterface("localhost", 8888)

    def testCoreSupport(self):
        sendData = []
        interface = SolrInterface("localhost", "8888", core="THE_CORE")
        interface._send = lambda path, body: sendData.append((path, body))
        list(interface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self.assertEquals(2, len(sendData))
        self.assertEquals(('/solr/THE_CORE/update', '<add><record><data>recordData</data></record></add>'), sendData[0])
        self.assertEquals(('/solr/THE_CORE/update', '<commit/>'), sendData[1])
        total, hits, path = self.executeQuery("meresco.exists:true", start=5, stop=10, sortBy="field", sortDescending=True, response=RESPONSE, solrInterface=interface)
        self.assertQuery("/solr/THE_CORE/select?q=meresco.exists%3Atrue&start=5&rows=5&sort=field+desc", path)

    def testAdd(self):
        g = compose(self._solrInterface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self._resultFromServerResponses(g, 2 * ["SOME RESPONSE"])

        g = compose(self._solrInterface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self.assertRaises(
            IOError,
            lambda: self._resultFromServerResponses(g, ["ERROR"], '500'))

        sendData = []
        self._solrInterface._send = lambda path, body: sendData.append((path, body))
        list(self._solrInterface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self.assertEquals(2, len(sendData))
        self.assertEquals(('/solr/update', '<add><record><data>recordData</data></record></add>'), sendData[0])
        self.assertEquals(('/solr/update', '<commit/>'), sendData[1])

    def testObservableName(self):
        sendData = []
        observable = Observable()
        solrInterface1 = SolrInterface("localhost", 1234, core="index1")
        solrInterface2 = SolrInterface("localhost", 1234, core="index2")
        solrInterface1._send = lambda path, body: sendData.append(("1", path, body))
        solrInterface2._send = lambda path, body: sendData.append(("2", path, body))
        observable.addObserver(solrInterface1)
        observable.addObserver(solrInterface2)

        list(compose(observable.all['index1'].add(identifier="recordId", partname="partname", data="data")))

        self.assertEquals([
                ('1', '/solr/index1/update', '<add>data</add>'),
                ('1', '/solr/index1/update', '<commit/>')
            ], sendData)

    def testDelete(self):
        g = compose(self._solrInterface.delete("record&:1"))
        self._resultFromServerResponses(g, 2 * ["SOME RESPONSE"])

        g = compose(self._solrInterface.delete("record&:1"))
        self.assertRaises(
            IOError,
            lambda: self._resultFromServerResponses(g, "ERROR", '500'))

        sendData = []
        self._solrInterface._send = lambda path, body: sendData.append((path, body))
        list(self._solrInterface.delete("record&:1"))
        self.assertEquals(2, len(sendData))
        self.assertEquals(('/solr/update', '<delete><id>%s</id></delete>' % "record&amp;:1"), sendData[0])
        self.assertEquals(('/solr/update', '<commit/>'), sendData[1])

    def testExecuteQuery(self):
        total, hits, path = self.executeQuery("meresco.exists:true", start=0, stop=10, sortBy=None, sortDescending=False, response=RESPONSE) 
        self.assertQuery("/solr/select?q=meresco.exists%3Atrue&start=0&rows=10", path)
        self.assertEquals(3, total)
        self.assertEquals(['1','3','5'], hits)

    def testExecuteEmptyQuery(self):
        self.assertRaises(ValueError, self.executeQuery, '', response=RESPONSE)

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
        self.assertQuery("/solr/select?facet.mincount=1&q=meresco.exists%3Atrue&start=0&rows=10&facet=on&facet.field=__all__&f.__all__.facet.sort=index&f.__all__.facet.limit=5", path)
        self.assertEquals(3, total)
        self.assertEquals(['1', '3', '5'], hits)
        self.assertEquals(['__all__'], result.keys())
        self.assertEquals([("term_0", 1), ("term_1", 2)], list(result['__all__']))

    def testExecuteQuerySolrHostFromObserver(self):
        solrInterface = SolrInterface()
        observer = CallTrace(returnValues={'solrServer': ('localhost', 1234)})
        solrInterface.addObserver(observer)
        args = []
        def httpget(*_args):
            args.append(_args)
            s = Suspend()
            response = yield s
            result = s.getResult()
            raise StopIteration(result)
        solrInterface._httpget = httpget

        g = compose(solrInterface.executeQuery("meresco.exists:true"))
        self._resultFromServerResponses(g, [RESPONSE])
        self.assertEquals(['solrServer'], observer.calledMethodNames())
        self.assertEquals([('localhost', 1234, '/solr/select?q=meresco.exists%3Atrue&start=0&rows=10')], args)

    def testAddWithSolrServerFromObserver(self):
        solrInterface = SolrInterface()
        observer = CallTrace(returnValues={'solrServer': ('localhost', 1234)})
        solrInterface.addObserver(observer)
        kwargs = []
        def httppost(**_kwargs):
            kwargs.append(_kwargs)
            s = Suspend()
            response = yield s
            result = s.getResult()
            raise StopIteration(result)
        solrInterface._httppost = httppost

        g = compose(solrInterface.add("recordId", "ignored", "<record><data>recordData</data></record>"))
        self._resultFromServerResponses(g, 2 * ["SOME RESPONSE"])
        self.assertEquals(['solrServer'] * 2, observer.calledMethodNames())
        self.assertEquals('localhost', kwargs[0]['host'])
        self.assertEquals(1234, kwargs[0]['port'])

    def testQueryResponseTime(self):
        response, readData = self.executeQueryResponse("meresco.exists:true", response=RESPONSE % "")
        self.assertEquals(6, response.queryTime)

    def executeQueryResponse(self, query, response, solrInterface=None, **kwargs):
        if solrInterface is None:
            solrInterface = self._solrInterface
        readData = []
        def read(path):
            readData.append(path)
        solrInterface._read = read
        gen = solrInterface.executeQuery(luceneQueryString=query, **kwargs)
        gen.next()
        try:
            gen.send(response)
        except StopIteration, e:
            (response,) = e.args 
            return response, readData
    
    def executeQuery(self, query, response, solrInterface=None, **kwargs):
        response, readData = self.executeQueryResponse(query, response, solrInterface=solrInterface, **kwargs)
        if getattr(response, 'drilldownData', None) is not None:
            return response.total, response.hits, response.drilldownData, readData[0]
        return response.total, response.hits, readData[0]

    def _resultFromServerResponses(self, g, serverResponses, responseStatus='200'):
        for response in serverResponses:
            s = g.next()
            self.assertEquals(Suspend, type(s))
            s(CallTrace('reactor'), lambda: None)
            s.resume('HTTP/1.1 %s\r\n\r\n%s' % (responseStatus, response))
        try:
            g.next()
            self.fail("expected StopIteration")
        except StopIteration, e:
            if len(e.args) > 0:
                return e.args[0]
    
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
        <int name="QTime">6</int>
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
            <str name="__id__">1</str>
        </doc>
        <doc>
            <str name="__id__">3</str>
        </doc>
        <doc>
            <str name="__id__">5</str>
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
