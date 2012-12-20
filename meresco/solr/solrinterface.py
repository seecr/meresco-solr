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

from urllib import urlencode
from lxml.etree import parse
from StringIO import StringIO
from xml.sax.saxutils import escape as escapeXml
from weightless.http import httpget, httppost
from meresco.core import Observable
from simplejson import loads

from solrresponse import SolrResponse


CRLF = '\r\n'

class SolrInterface(Observable):
    COUNT = 'count'
    INDEX = 'index'
    SUPPORTED_SORTBY_VALUES = [COUNT, INDEX]

    def __init__(self, host=None, port=None, core=None, commitTimeout=1):
        Observable.__init__(self)
        self._host = host
        self._port = port
        self._core = core
        self._commitWithin = int(commitTimeout * 1000)
        if self._commitWithin <= 0:
            raise ValueError("Value commitTimeout should be greater then zero")
        if core is not None:
            self.observable_name = lambda: core

    def all_unknown(self, message, *args, **kwargs):
        print 'Unexpected all.unknown for:', message, args, kwargs
        return
        yield

    def do_unknown(self, message, *args, **kwargs):
        print 'Unexpected do.unknown for:', message, args, kwargs

    def _path(self, action):
        return '/solr/%s' % action if self._core is None else '/solr/%s/%s' % (self._core, action)

    def add(self, identifier, data, **kwargs):
        path = self._path('update')
        path += "?commitWithin=%d" % self._commitWithin
        yield self._send(path=path, body="<add>%s</add>" % data)

    def delete(self, identifier):
        path = self._path('update')
        path += "?commitWithin=%d" % self._commitWithin
        yield self._send(path=path, body="<delete><id>%s</id></delete>" % escapeXml(identifier))

    def executeQuery(self, luceneQueryString, start=0, stop=10, sortKeys=None, suggestionsCount=0, suggestionsQuery=None, filterQuery=None, facets=None, **kwargs):
        if not luceneQueryString:
            raise ValueError("Empty luceneQueryString not allowed.")
        arguments = dict(
                q=luceneQueryString, 
                start=start, 
                rows=stop-start, 
                wt='json'
            )
        if sortKeys:
            arguments["sort"] = ','.join("%s %s" % (sortKey['sortBy'], 'desc' if sortKey['sortDescending'] else 'asc') for sortKey in sortKeys)
        if filterQuery:
            arguments['fq'] = filterQuery

        arguments.update(_facetArguments(facets))
        if suggestionsCount > 0 and suggestionsQuery:
            arguments["spellcheck"] = 'true'
            arguments["spellcheck.count"] = suggestionsCount
            arguments["spellcheck.q"] = suggestionsQuery

        path = self._path('select')
        body = yield self._send(path, urlencode(arguments, doseq=True), contentType='application/x-www-form-urlencoded')
        jsonResponse = loads(body)
        recordCount = jsonResponse['response']['numFound']
        identifiers = [doc.values()[0] for doc in jsonResponse['response']['docs']]
        qtime = jsonResponse['responseHeader']['QTime']
        response = SolrResponse(total=recordCount, hits=identifiers, queryTime=qtime)
        if not facets is None:
             _updateResponseWithDrilldownData(arguments, jsonResponse['facet_counts'], response)
        if suggestionsCount > 0 and suggestionsQuery:
            _updateResponseWithSuggestionData(arguments, jsonResponse['spellcheck']['suggestions'], response)
        raise StopIteration(response)

    def prefixSearch(self, field, prefix, limit=10):
        arguments = {'terms.fl': field, 'terms.prefix': prefix, 'terms.limit': limit}
        path = self._path('terms')
        body = yield self._send(path, urlencode(arguments, doseq=True), contentType='application/x-www-form-urlencoded')
        xml = parse(StringIO(body))
        terms = xml.xpath('/response/lst[@name="terms"]/lst[@name="%s"]/int/@name' % field)
        qtime = int(xml.xpath('/response/lst[@name="responseHeader"]/int[@name="QTime"]/text()')[0])
        response = SolrResponse(total=len(terms), hits=terms, queryTime=qtime)
        raise StopIteration(response)
    
    def fieldnames(self):
        path = self._path('admin/luke')
        body = yield self._read(path)
        xml = parse(StringIO(body))
        fieldnames = xml.xpath('/response/lst[@name="fields"]/lst/@name')
        qtime = int(xml.xpath('/response/lst[@name="responseHeader"]/int[@name="QTime"]/text()')[0])
        response = SolrResponse(total=len(fieldnames), hits=fieldnames, queryTime=qtime)
        raise StopIteration(response)

    def _send(self, path, body, contentType="text/xml"):
        headers = None
        if body:
             headers={'Content-Type': contentType, 'Content-Length': len(body)}
        host, port = self._solrServer() # WARNING: can return a different server each time.
        response = yield self._httppost(host=host, port=port, request=path, body=body, headers=headers)
        header, body = response.split("\r\n\r\n", 1)
        self._verify200(header, response)
        raise StopIteration(body)

    def _read(self, path):
        host, port = self._solrServer()
        response = yield self._httpget(host, port, path)
        header, body = response.split('\r\n\r\n', 1)
        self._verify200(header, response)
        raise StopIteration(body)

    def _httpget(self, *args):
        return httpget(*args)

    def _httppost(self, **kwargs):
        return httppost(**kwargs)

    def _verify200(self, header, response):
        if not header.startswith('HTTP/1.1 200'):
            raise IOError("Expected status '200' from Solr, but got: " + response)

    def _solrServer(self):
        return (self._host, self._port) if self._host else self.call.solrServer()

def _facetArguments(facets):
    def facetLimit(facet):
        maxTerms = facet.get('maxTerms', None)
        arguments.setdefault('f.%s.facet.limit' % facet['field'], []).append(maxTerms if maxTerms else -1)

    def facetSort(facet):
        sortBy = facet.get('sortBy', None)
        if sortBy is not None:
            if not sortBy in SolrInterface.SUPPORTED_SORTBY_VALUES:
                raise ValueError("'sortBy' should be one of %s" % SolrInterface.SUPPORTED_SORTBY_VALUES)
            arguments.setdefault('f.%s.facet.sort' % facet['field'], []).append(sortBy)

    arguments = {}
    if facets is not None:
        arguments['facet'] = "on"
        arguments['facet.mincount'] = "1"
        arguments['facet.field'] = []
        for facet in facets:
            if isinstance(facet, dict):
                arguments['facet.field'].append(facet['field'])
                facetLimit(facet)
                facetSort(facet)
            else:
                arguments["facet.pivot"] = ','.join(f['field'] for f in facet)
                arguments['facet.pivot.mincount'] = "0"
                for f in facet:
                    facetLimit(f)
                    facetSort(f)
    return arguments

def _updateResponseWithDrilldownData(arguments, facetCounts, response):
    drilldownData = []
    for fieldname, termCounts in facetCounts['facet_fields'].items():
        terms = []
        for i in xrange(0, len(termCounts), 2):
            terms.append({'term': termCounts[i], 'count': termCounts[i+1]})
        drilldownData.append(dict(fieldname=fieldname, terms=terms))
    if 'facet_pivot' in facetCounts:
        for drilldown in facetCounts['facet_pivot'].values():
            drilldownData.append(_buildDrilldownDict(drilldown))
    response.drilldownData = drilldownData

def _buildDrilldownDict(drilldown):
    fieldname = drilldown[0]['field']
    terms = []
    for d in drilldown:
        termDict = {'term': d['value'], 'count': d['count']}
        if 'pivot' in d:
            pivot = d['pivot']
            if pivot:
                termDict['pivot'] = _buildDrilldownDict(pivot)
        terms.append(termDict)
    return dict(fieldname=fieldname, terms=terms)

def _updateResponseWithSuggestionData(arguments, spellcheckResult, response):
    suggestions = {}
    for i in xrange(0, len(spellcheckResult), 2):
        name = spellcheckResult[i]
        suggestion = spellcheckResult[i+1]
        suggestions[name] = (suggestion['startOffset'], suggestion['endOffset'], suggestion['suggestion'])
    response.suggestions = suggestions
