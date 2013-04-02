# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2012-2013 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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
        sleep(1)
        
        response = self.solrRequest(luceneQueryString='__id__:record\:testAddQueryDelete')
        self.assertEquals(1, response['total'])
        self.assertEquals(['record:testAddQueryDelete'], response['hits'])

        header, body = postRequest(port=self.solrClientPort, path='/delete', data=dumps(dict(identifier='record:testAddQueryDelete')), parse=False)
        self.assertEquals('', body)
        sleep(1)

        response = self.solrRequest(luceneQueryString='__id__:record\:testAddQueryDelete')
        self.assertEquals(0, response['total'])

    def testDatabase(self):
        response = self.solrRequest(luceneQueryString='*:*')
        self.assertEquals(69, response['total'])

    def testAsciiFoldingFilterFactoryForTextWSFields(self):
        response = self.solrRequest(luceneQueryString='Morée')
        self.assertEquals(1, response['total'])
        response = self.solrRequest(luceneQueryString='Moree')
        self.assertEquals(1, response['total'])
        response = self.solrRequest(luceneQueryString='Morèe')
        self.assertEquals(1, response['total'])
        response = self.solrRequest(luceneQueryString='More\u0301e')
        self.assertEquals(0, response['total'])

    def testPivoting(self):
        response = self.solrRequest(luceneQueryString='*:*', facets=[
            [{'fieldname': 'untokenized.rdf:type', 'maxTerms': 2}, {'fieldname': 'untokenized.dc:date', 'maxTerms': 2}]            
        ])
        self.assertEquals([
            {
                "fieldname": "untokenized.rdf:type", 
                "terms": [
                    {
                        "count": 46, 
                        "pivot": {
                            "fieldname": "untokenized.dc:date", 
                            "terms": [
                                {
                                    "count": 5, 
                                    "term": "1975"
                                }, 
                                {
                                    "count": 4, 
                                    "term": "1971"
                                }, 
                            ]
                        }, 
                        "term": "http://dbpedia.org/ontology/Book"
                    }, 
                    {
                        "count": 4, 
                        "term": "http://www.w3.org/2004/02/skos/core#Concept"
                    }, 
                ]
            }
        ], response['drilldownData'])

    def testPivotingMultipleFacets(self):
        response = self.solrRequest(luceneQueryString='*:*', facets=[
            [{'fieldname': 'untokenized.rdf:type', 'maxTerms': 2}, {'fieldname': 'untokenized.dc:date', 'maxTerms': 2}],
            [{'fieldname': 'untokenized.dc:subject', 'maxTerms': 2}, {'fieldname': 'untokenized.dc:date', 'maxTerms': 2}],
        ])
        self.assertEquals([
            {
                "fieldname": "untokenized.rdf:type", 
                "terms": [
                    {
                        "count": 46, 
                        "pivot": {
                            "fieldname": "untokenized.dc:date", 
                            "terms": [
                                {
                                    "count": 5, 
                                    "term": "1975"
                                }, 
                                {
                                    "count": 4, 
                                    "term": "1971"
                                }, 
                            ]
                        }, 
                        "term": "http://dbpedia.org/ontology/Book"
                    }, 
                    {
                        "count": 4, 
                        "term": "http://www.w3.org/2004/02/skos/core#Concept"
                    }, 
                ]
            },
            {'fieldname': 'untokenized.dc:subject',
                'terms': [{
                    'count': 1, 
                    'pivot': {
                        'fieldname': 'untokenized.dc:date', 
                        'terms': [{
                            'count': 1, 
                            'term': '1975'
                        }]
                    }, 
                    'term': 'Bourbonnais (France)'
                }, {
                    'count': 1, 
                    'pivot': {
                        'fieldname': 'untokenized.dc:date', 
                        'terms': [{
                            'count': 1, 
                            'term': '1966'
                        }]
                    }, 
                    'term': 'Doesburg (Netherlands)'
                }]
            }
        ], response['drilldownData'])

    def testPrefixSearch(self):
        response = self.solrRequest(path='/prefixSearch', prefix="cha", fieldname='__all__')
        self.assertEquals(['charles', 'challenge', 'chamber'], response['hits'])

    def testFieldnames(self):
        response = self.solrRequest(path='/fieldnames')
        fields = response['hits']
        self.assertEquals(28, len(fields))
        self.assertTrue('__all__' in fields, fields)

    def testSuggestions(self):
        response = self.solrRequest(path='/executeQuery', luceneQueryString="*:*", suggestionsQuery='*', suggestionsCount=5)
        self.assertFalse('suggestions' in response, response)

        response = self.solrRequest(path='/executeQuery', luceneQueryString="*:*", suggestionsQuery='callenge', suggestionsCount=5)
        self.assertEquals([0, 8, ['challenge', 'college', 'vallen', 'alleen', 'gallery']], response['suggestions']['callenge'])

    def solrRequest(self, path="/executeQuery", **queryKwargs):
        header, body = postRequest(port=self.solrClientPort, path=path, data=dumps(queryKwargs), parse=False)
        responseType, responseDict = body.split(': ', 1)
        self.assertEquals('SolrResponse', responseType, responseType + responseDict)
        return loads(responseDict)
