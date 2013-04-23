## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from cgi import parse_qs

from weightless.core import compose
from weightless.io import Suspend
from meresco.core import Observable
from meresco.solr.solrinterface import SolrInterface
from seecr.test import CallTrace, SeecrTestCase


class SolrInterfaceTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self._solrInterface = SolrInterface("localhost", 8888)

    def testCoreSupport(self):
        sendData = []
        interface = SolrInterface("localhost", "8888", core="THE_CORE")
        interface._send = lambda path, body: sendData.append((path, body))
        list(interface.add(identifier="recordId", partname="ignored", data="<record><data>recordData</data></record>"))
        self.assertEquals(1, len(sendData))
        self.assertEquals(('/solr/THE_CORE/update', '<add><record><data>recordData</data></record></add>'), sendData[0])
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", start=5, stop=10, sortKeys=[dict(sortBy="field", sortDescending=True)], response=JSON_RESPONSE % "", solrInterface=interface)
        self.assertEquals(path, "/solr/THE_CORE/select")
        self.assertQueryArguments("q=meresco.exists%3Atrue&start=5&rows=5&sort=field+desc&wt=json", body)

    def testAdd(self):
        g = compose(self._solrInterface.add(identifier="recordId", partname="ignored", data="<record><data>recordData</data></record>"))
        self._returnValueFromGenerator(g, ["SOME RESPONSE"])

        g = compose(self._solrInterface.add(identifier="recordId", partname="ignored", data="<record><data>recordData</data></record>"))
        self.assertRaises(
            IOError,
            lambda: self._returnValueFromGenerator(g, ["ERROR"], '500'))

        sendData = []
        self._solrInterface._send = lambda path, body: sendData.append((path, body))
        list(self._solrInterface.add(identifier="recordId", partname="ignored", data="<record><data>recordData</data></record>"))
        self.assertEquals(1, len(sendData))
        self.assertEquals(('/solr/update', '<add><record><data>recordData</data></record></add>'), sendData[0])

    def testAddWithTimeOut(self):
        sent_data = []
        iSolr = SolrInterface("localhost", "8889")
        iSolr._send = lambda path, body: sent_data.append((path, body))
        r = iSolr.add(identifier="record1", partname="part0", data="<record><data>data here</data></record>")
        list(r)
        self.assertEquals('/solr/update', sent_data[0][0])
        self.assertEquals(1, len(sent_data))

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
            ], sendData)

    def testDelete(self):
        g = compose(self._solrInterface.delete("record&:1"))
        self._returnValueFromGenerator(g, ["SOME RESPONSE"])

        g = compose(self._solrInterface.delete("record&:1"))
        self.assertRaises(
            IOError,
            lambda: self._returnValueFromGenerator(g, "ERROR", '500'))

        sendData = []
        self._solrInterface._send = lambda path, body: sendData.append((path, body))
        list(self._solrInterface.delete("record&:1"))
        self.assertEquals(1, len(sendData))
        self.assertEquals(('/solr/update', '<delete><id>%s</id></delete>' % "record&amp;:1"), sendData[0])

    def testDeleteWithTimeOut(self):
        sent_data = []
        iSolr = SolrInterface("localhost", "8889")
        iSolr._send = lambda path, body: sent_data.append((path, body))
        r = iSolr.delete("record1")
        list(r)
        self.assertEquals('/solr/update', sent_data[0][0])
        self.assertEquals(1, len(sent_data))

    def testExecuteQuery(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", start=0, stop=10, sortKeys=None, response=JSON_RESPONSE % "") 
        self.assertEquals("/solr/select", path)
        self.assertQueryArguments("q=meresco.exists%3Atrue&start=0&rows=10&wt=json", body)
        self.assertEquals(3, response.total)
        self.assertEquals(['1','3','5'], response.hits)

    def testPrefixSearch(self):
        response, (path, body) = self.executePrefixSearch(prefix="ho", fieldname="afield", response=TERMS_PREFIX_RESPONSE) 
        self.assertEquals(['hoogte', 'holland', 'hoe', 'horticulture', 'houden', 'housing', 'houdt', 'hoge', 'hoofd', 'houten'], response.hits)
        self.assertEquals(10, response.total)
        self.assertEquals(76, response.queryTime)
        self.assertEquals('/solr/terms', path)
        self.assertQueryArguments('terms.limit=10&terms.prefix=ho&terms.fl=afield&wt=json', body)

    def testPrefixSearchWithLimit(self):
        response, (path, body) = self.executePrefixSearch(prefix="ho", fieldname="afield", limit=5, response=TERMS_PREFIX_RESPONSE) 
        self.assertEquals('/solr/terms', path)
        self.assertQueryArguments('terms.limit=5&terms.prefix=ho&terms.fl=afield&wt=json', body)

    def testExecuteEmptyQuery(self):
        self.assertRaises(ValueError, self.executeQueryResponse, '', response=JSON_RESPONSE % "")

    def testExecuteQueryWithStartStopAndSortKeys(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", start=5, stop=10, sortKeys=[dict(sortBy="field", sortDescending=True), dict(sortBy="anotherfield", sortDescending=False)], response=JSON_RESPONSE % "")
        self.assertEquals("/solr/select", path)
        self.assertQueryArguments("q=meresco.exists%3Atrue&start=5&rows=5&sort=field+desc,anotherfield+asc&wt=json", body)
        self.assertEquals(3, response.total)
        self.assertEquals(['1','3','5'], response.hits)

    def testExecuteQuerySortAscending(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", start=0, stop=10, sortKeys=[dict(sortBy="field", sortDescending=False)], response=JSON_RESPONSE % "")
        self.assertEquals("/solr/select", path)
        self.assertQueryArguments("q=meresco.exists%3Atrue&start=0&rows=10&sort=field+asc&wt=json", body)
        self.assertEquals(3, response.total)
        self.assertEquals(['1','3','5'], response.hits)

    def testDrilldown(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", facets=[{'fieldname': '__all__', 'maxTerms': 5, "sortBy": "count"}, {'fieldname': '__other__', 'maxTerms': 5, 'sortBy': "index"}], response=JSON_RESPONSE % JSON_FACET_COUNTS)
        self.assertEquals("/solr/select", path)
        self.assertQueryArguments("wt=json&facet.mincount=1&q=meresco.exists%3Atrue&start=0&rows=10&facet=on&facet.field=__all__&f.__all__.facet.sort=count&f.__all__.facet.limit=5&facet.field=__other__&f.__other__.facet.limit=5&f.__other__.facet.sort=index", body)
        self.assertEquals(3, response.total)
        self.assertEquals(['1', '3', '5'], response.hits)
        self.assertEquals(['__all__', '__other__'], [f['fieldname'] for f in response.drilldownData])
        self.assertEquals([{'term': "term_0", 'count': 1}, {'term': "term_1", 'count': 2}], response.drilldownData[0]['terms'])
        self.assertEquals([{'term': "term_2", 'count': 3}, {'term': "term_3", 'count': 4}], response.drilldownData[1]['terms'])

    def testDrilldownUnsupportedSortBy(self):
        self.assertRaises(ValueError, lambda: self.executeQueryResponse("meresco.exists:true", facets=[{'fieldname': '__all__', 'maxTerms': 5, "sortBy": "timestamp"}], response=JSON_RESPONSE % JSON_FACET_COUNTS))

    def testDrilldownOnSameFieldTwice(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", facets=[{'fieldname': '__all__', 'maxTerms': 5, "sortBy": "index"}, {'fieldname': '__all__', 'maxTerms': 5, 'sortBy': "index"}], response=JSON_RESPONSE % JSON_FACET_COUNTS_SAME_FIELD_TWICE)
        self.assertQueryArguments("wt=json&facet.mincount=1&q=meresco.exists%3Atrue&start=0&rows=10&facet=on&facet.field=__all__&f.__all__.facet.sort=index&f.__all__.facet.limit=5&facet.field=__all__&f.__all__.facet.limit=5&f.__all__.facet.sort=index", body)
        self.assertEquals(3, response.total)
        self.assertEquals(['1', '3', '5'], response.hits)
        self.assertEquals(1, len(response.drilldownData))
        self.assertEquals(['__all__'], [f['fieldname'] for f in response.drilldownData])
        self.assertEquals([{'term': "term_0", 'count': 1}, {'term': "term_1", 'count': 2}], response.drilldownData[0]['terms'])

    def testPivotDrilldown(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", facets=[
                [
                    {'fieldname': '__all__', 'sortBy': 'index'},
                    {'fieldname': '__other__', 'maxTerms': 5}
                ], 
                {'fieldname': '__field1__', 'maxTerms': 2, 'sortBy': 'count'},
                {'fieldname': '__field2__', 'maxTerms': None}
            ], response=JSON_RESPONSE % JSON_FACET_WITH_PIVOT)
        arguments = parse_qs(body, keep_blank_values=True)
        self.assertEquals(['1'], arguments['facet.mincount'])
        self.assertEquals(['meresco.exists:true'], arguments['q'])
        self.assertEquals(['0'], arguments['start'])
        self.assertEquals(['10'], arguments['rows'])
        self.assertEquals(['on'], arguments['facet'])
        self.assertEquals(['__all__,__other__'], arguments['facet.pivot'])
        self.assertEquals(['__field1__', '__field2__'], arguments['facet.field'])
        self.assertEquals(['count'], arguments['f.__field1__.facet.sort'])
        self.assertEquals(['index'], arguments['f.__all__.facet.sort'])
        self.assertEquals(['2'], arguments['f.__field1__.facet.limit'])
        self.assertEquals(['-1'], arguments['f.__all__.facet.limit'])
        self.assertEquals(['5'], arguments['f.__other__.facet.limit'])
        self.assertEquals(['-1'], arguments['f.__field2__.facet.limit'])
        self.assertEqualsWS(repr([
                {
                    'fieldname': '__field2__',
                    'terms': [
                        {
                            'term': '4',
                            'count': 4
                        },
                        {
                            'term': '5',
                            'count': 5
                        },
                        {
                            'term': '6',
                            'count': 6
                        }
                    ]
                },
                {
                    'fieldname': '__field1__',
                    'terms': [
                        {
                            'term': '1',
                            'count': 1
                        },
                        {
                            'term': '2',
                            'count': 2
                        },
                        {
                            'term': '3',
                            'count': 3
                        }
                    ]
                },
                {
                    'fieldname': '__all__',
                    'terms': [
                        {
                            'term': 'all:1',
                            'count': 1,
                            'pivot': {
                                'fieldname': '__other__',
                                'terms': [
                                    {
                                        'term': 'other:1',
                                        'count': 1
                                    },
                                    {
                                        'term': 'other:2',
                                        'count': 2
                                    }
                                ]
                            }
                        },
                        {
                            'term': 'all:2',
                            'count': 2,
                            'pivot': {
                                'fieldname': '__other__',
                                'terms': [
                                    {
                                        'term': 'other:3',
                                        'count': 3
                                    },
                                    {
                                        'term': 'other:4',
                                        'count': 4
                                    }
                                ]
                            }
                        },
                        {
                            'term': 'all:3',
                            'count': 2
                        }
                    ]
                }
            ]), repr(response.drilldownData))

    def testPivotDrilldownNoResponse(self):
        response, (path, body) = self.executeQueryResponse("meresco.exists:true", facets=[
                [
                    {'fieldname': '__all__', 'sortBy': 'index'},
                    {'fieldname': '__other__', 'maxTerms': 5}
                ], 
            ], response=JSON_RESPONSE % JSON_FACET_WITH_PIVOT_NO_RESPONSE)
        parse_qs(body, keep_blank_values=True)
        self.assertEqualsWS(repr([
            ]), repr(response.drilldownData))

    def testExecuteQuerySolrHostFromObserver(self):
        solrInterface = SolrInterface()
        observer = CallTrace(returnValues={'solrServer': ('localhost', 1234)})
        solrInterface.addObserver(observer)
        kwargs = []
        def httppost(**_kwargs):
            kwargs.append(_kwargs)
            s = Suspend()
            yield s
            result = s.getResult()
            raise StopIteration(result)
        solrInterface._httppost = httppost

        g = compose(solrInterface.executeQuery("meresco.exists:true"))
        self._returnValueFromGenerator(g, [JSON_RESPONSE % ""])
        self.assertEquals(['solrServer'], observer.calledMethodNames())
        self.assertQueryArguments('q=meresco.exists%3Atrue&start=0&rows=10&wt=json', kwargs[0]['body'])
        self.assertEquals('localhost', kwargs[0]['host'])
        self.assertEquals('/solr/select', kwargs[0]['request'])
        self.assertEquals(1234, kwargs[0]['port'])
        self.assertEquals({'Content-Type': 'application/x-www-form-urlencoded', 'Content-Length': len(kwargs[0]['body'])}, kwargs[0]['headers'])

    def testAddWithSolrServerFromObserver(self):
        solrInterface = SolrInterface()
        observer = CallTrace(returnValues={'solrServer': ('localhost', 1234)})
        solrInterface.addObserver(observer)
        kwargs = []
        def httppost(**_kwargs):
            kwargs.append(_kwargs)
            s = Suspend()
            yield s
            result = s.getResult()
            raise StopIteration(result)
        solrInterface._httppost = httppost

        g = compose(solrInterface.add(identifier="recordId", partname="ignored", data="<record><data>recordData</data></record>"))
        self._returnValueFromGenerator(g, ["SOME RESPONSE"])
        self.assertEquals(['solrServer'], observer.calledMethodNames())
        self.assertEquals('localhost', kwargs[0]['host'])
        self.assertEquals(1234, kwargs[0]['port'])
        self.assertEquals({'Content-Type': 'text/xml', 'Content-Length': len(kwargs[0]['body'])}, kwargs[0]['headers'])

    def testQueryResponseTime(self):
        response, readData = self.executeQueryResponse("meresco.exists:true", response=JSON_RESPONSE % "")
        self.assertEquals(6, response.queryTime)

    def testSolrGivesSpellCheckResults(self):
        response, (path, body) = self.executeQueryResponse(query="__all__:aap AND __all__:bo", response=JSON_RESPONSE % JSON_SUGGESTIONS, suggestionsCount=2, suggestionsQuery="aap AND bo")
        self.assertQueryArguments('spellcheck.count=2&rows=10&spellcheck=true&spellcheck.q=aap+AND+bo&q=__all__%3Aaap+AND+__all__%3Abo&start=0&wt=json', body)
        self.assertEquals(['1','3','5'], response.hits)
        self.assertEquals({'aap': (0, 3, ['aapje', 'raap']), 'bo': (8, 10, ['bio', 'bon'])}, response.suggestions)

    def testFieldnames(self):
        readData = []
        def read(path, arguments):
            readData.append((path, arguments))
        self._solrInterface._read = read
        gen = self._solrInterface.fieldnames()
        gen.next()
        try:
            gen.send(FIELDNAMES_RESPONSE)
        except StopIteration, e:
            (response,) = e.args 
        self.assertEquals([('/solr/admin/luke', {'wt': 'json'})], readData)
        self.assertEquals(sorted(['__all__', '__exists__', '__id__', '__timestamp__', 'field0', 'field1', 'untokenized.field0']), sorted(response.hits))

    def testPassfilterQueries(self):
        response, (path, body) = self.executeQueryResponse("*", filterQueries=["field:value"], response=JSON_RESPONSE % "") 
        self.assertQueryArguments("q=*&fq=field:value&start=0&rows=10&wt=json", body)
        response, (path, body) = self.executeQueryResponse("*", filterQueries=["field:http\://host.nl"], response=JSON_RESPONSE % "") 
        self.assertQueryArguments("q=*&fq=field:http\://host.nl&start=0&rows=10&wt=json", body)

    def testJoinQueries(self):
        response, (path, body) = self.executeQueryResponse("*", joinQueries=[dict(core='aCore', fromField='field0', toField='field1', query='aQuery')], response=JSON_RESPONSE % "")
        self.assertQueryArguments("q=*&fq={!join fromIndex=aCore from=field0 to=field1}aQuery&start=0&rows=10&wt=json", body)

    def testJoinFacets(self):
        response, (path, body) = self.executeQueryResponse("*", joinFacets=[dict(core='aCore', fromField='field0', toField='field1', facetField='field2')], response=JSON_RESPONSE % "")
        self.assertQueryArguments("q=*&facet=on&facet.mincount=1&joinFacet.field={!facetjoin core=aCore from=field0 to=field1}field2&start=0&rows=10&wt=json", body)


    def executeQueryResponse(self, query, response, solrInterface=None, **kwargs):
        if solrInterface is None:
            solrInterface = self._solrInterface
        sendData = []
        def send(path, body, contentType="default"):
            sendData.append((path, body))
        solrInterface._send = send
        gen = solrInterface.executeQuery(luceneQueryString=query, **kwargs)
        gen.next()
        try:
            gen.send(response)
        except StopIteration, e:
            (response,) = e.args
            return response, sendData[0]

    def executePrefixSearch(self, response, solrInterface=None, **kwargs):
        if solrInterface is None:
            solrInterface = self._solrInterface
        sendData = []
        def send(path, body, contentType="default"):
            sendData.append((path, body))
        solrInterface._send = send
        gen = solrInterface.prefixSearch(**kwargs)
        gen.next()
        try:
            gen.send(response)
        except StopIteration, e:
            (response,) = e.args
            return response, sendData[0]
    
    def _returnValueFromGenerator(self, g, serverResponses, responseStatus='200'):
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
    
    def assertQueryArguments(self, arguments1, arguments2):
        arguments1 = parse_qs(arguments1, keep_blank_values=True)
        arguments2 = parse_qs(arguments2, keep_blank_values=True)
        self.assertEquals(arguments1, arguments2)

TERMS_PREFIX_RESPONSE = """
{
    "responseHeader": 
    {
        "status":0,
        "QTime":76
    },
    "terms":
    {
        "afield":[
            "hoogte",221194,
            "holland",162140,
            "hoe",57391,
            "horticulture",30914,
            "houden",15239,
            "housing",14980,
            "houdt",14178,
            "hoge",12870,
            "hoofd",12583,
            "houten",10945
        ]
    }
}"""

JSON_SUGGESTIONS = """,
"spellcheck":{
    "suggestions":[
        "aap",{
            "numFound":2,
            "startOffset":0,
            "endOffset":3,
            "suggestion":[
                "aapje","raap"
            ]
        },
        "bo",{
            "numFound":2,
            "startOffset":8,
            "endOffset":10,
            "suggestion":[
                "bio","bon"
            ]
        }
    ]
}
"""

JSON_FACET_COUNTS = """,
"facet_counts":{
    "facet_queries":{},
    "facet_fields":{
        "__all__":["term_0",1,"term_1",2],
        "__other__":["term_2",3,"term_3",4]
    },
    "facet_dates": {},
    "facet_ranges": {}
}"""

JSON_FACET_COUNTS_SAME_FIELD_TWICE = """,
"facet_counts":{
    "facet_queries":{},
    "facet_fields":{
        "__all__":["term_0",1,"term_1",2],
        "__all__":["term_0",1,"term_1",2]
    },
    "facet_dates": {},
    "facet_ranges": {}
}"""

FIELDNAMES_RESPONSE="""
{
    "responseHeader":{
        "status":0,
        "QTime":2
    },
    "index":{
        "numDocs":69,
        "maxDoc":69,
        "version":7,
        "segmentCount":1,
        "current":true,
        "hasDeletions":false,
        "directory":"org.apache.lucene.store.NRTCachingDirectory:NRTCachingDirectory(org.apache.lucene.store.MMapDirectory@/tmp/integrationtest-solr-default/solr/cores/records/data/index lockFactory=org.apache.lucene.store.NativeFSLockFactory@7d0c3a08; maxCacheMB=48.0 maxMergeSizeMB=4.0)",
        "userData":{}
    },
    "fields": {
        "__all__": {
            "type":"text_ws",
            "schema":"IT-M----------",
            "index":"(unstored field)",
            "docs":62
        },
        "__exists__": "...",
        "__id__": "...",
        "__timestamp__": "...",
        "field0": "...",
        "field1": "...",
        "untokenized.field0": "..."
    }
}"""


JSON_RESPONSE = """
{
    "responseHeader":{
        "status":0,
        "QTime":6
    },
    "response":{
        "numFound":3,
        "start":0,
        "docs":[{"__id__": "1"}, {"__id__": "3"}, {"__id__": "5"}]
    }
    %s
}"""

JSON_FACET_WITH_PIVOT = """,
"facet_counts":{
    "facet_queries":{},
    "facet_fields":{
        "__field1__":["1",1,"2",2,"3",3],
        "__field2__":["4",4,"5",5,"6",6]
    },
    "facet_dates":{},
    "facet_ranges":{},
    "facet_pivot":{
        "__all__,__other__":[
            {
                "field":"__all__",
                "value":"all:1",
                "count":1,
                "pivot":[
                    {
                        "field":"__other__",
                        "value":"other:1",
                        "count":1
                    },
                    {
                        "field":"__other__",
                        "value":"other:2",
                        "count":2
                    }
                ]
            },
            {
                "field":"__all__",
                "value":"all:2",
                "count":2,
                "pivot":[
                    {
                        "field":"__other__",
                        "value":"other:3",
                        "count":3
                    },
                    {
                        "field":"__other__",
                        "value":"other:4",
                        "count":4
                    }
                ]
            },
            {
                "field":"__all__",
                "value":"all:3",
                "count":2,
                "pivot":[]
            }
        ]
    }
}"""

JSON_FACET_WITH_PIVOT_NO_RESPONSE = """,
"facet_counts":{
    "facet_queries":{},
    "facet_dates":{},
    "facet_fields":{},
    "facet_ranges":{},
    "facet_pivot":{
        "__all__,__other__":[]
    }
}"""
