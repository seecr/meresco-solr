## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
from xml.sax.saxutils import escape as escapeXml
from weightless.http import httpget, httppost
from meresco.core import Observable
from simplejson import loads

from solrresponse import SolrResponse

UNTOKENIZED_PREFIX = 'untokenized.'
JOINHASH_PREFIX = 'joinhash.'
SORTED_PREFIX = 'sorted.'


class SolrInterface(Observable):
    COUNT = 'count'
    INDEX = 'index'
    SUPPORTED_SORTBY_VALUES = [COUNT, INDEX]

    def __init__(self, host=None, port=None, core=None):
        Observable.__init__(self)
        self._host = host
        self._port = port
        self._core = core
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
        yield self._send(path=path, body="<add>%s</add>" % data)

    def delete(self, identifier):
        path = self._path('update')
        yield self._send(path=path, body="<delete><id>%s</id></delete>" % escapeXml(identifier))

    def executeQuery(self, luceneQueryString, start=0, stop=10, sortKeys=None, suggestionRequest=None, filterQueries=None, joinQueries=None, facets=None, joinFacets=None, **kwargs):
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

        filterQueries = filterQueries or []
        filterQueries.extend(_joinQueriesAsFilterQueries(joinQueries))
        if filterQueries:
            arguments['fq'] = filterQueries

        arguments.update(_facetArguments(facets, joinFacets))
        if suggestionRequest:
            arguments["spellcheck"] = 'true'
            arguments["spellcheck.count"] = suggestionRequest['count']
            arguments["spellcheck.q"] = suggestionRequest['query']

        path = self._path('select')
        body = yield self._send(path, urlencode(arguments, doseq=True), contentType='application/x-www-form-urlencoded')
        jsonResponse = loads(body)
        recordCount = jsonResponse['response']['numFound']
        identifiers = [doc.values()[0] for doc in jsonResponse['response']['docs']]
        qtime = jsonResponse['responseHeader']['QTime']
        response = SolrResponse(total=recordCount, hits=identifiers, queryTime=qtime)
        if 'facet_counts' in jsonResponse:
             _updateResponseWithDrilldownData(arguments, jsonResponse['facet_counts'], response)
        if suggestionRequest and 'spellcheck' in jsonResponse:
            _updateResponseWithSuggestionData(arguments, jsonResponse['spellcheck']['suggestions'], response)
        raise StopIteration(response)

    def prefixSearch(self, fieldname, prefix, limit=10):
        arguments = {'terms.fl': fieldname, 'terms.prefix': prefix, 'terms.limit': limit, 'wt': 'json'}
        path = self._path('terms')
        body = yield self._send(path, urlencode(arguments, doseq=True), contentType='application/x-www-form-urlencoded')
        jsonResponse = loads(body)
        terms = jsonResponse['terms'][fieldname][::2]
        qtime = jsonResponse['responseHeader']['QTime']
        response = SolrResponse(total=len(terms), hits=terms, queryTime=qtime)
        raise StopIteration(response)

    def fieldnames(self):
        path = self._path('admin/luke')
        body = yield self._read(path, arguments={'wt': 'json'})
        jsonResponse = loads(body)
        fieldnames = jsonResponse['fields'].keys()
        qtime = jsonResponse['responseHeader']['QTime']
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

    def _read(self, path, arguments=None):
        host, port = self._solrServer()
        if arguments:
            path += '?' + urlencode(arguments, doseq=True)
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


def _joinQueriesAsFilterQueries(joinQueries):
    joinQueries = joinQueries or []
    for joinQuery in joinQueries:
        yield '{!join fromIndex=%(core)s from=%(fromField)s to=%(toField)s}%(query)s' % joinQuery


def _facetArguments(facets, joinFacets):
    def facetLimit(facet):
        maxTerms = facet.get('maxTerms', None)
        arguments.setdefault('f.%s.facet.limit' % facet['fieldname'], []).append(maxTerms if maxTerms else -1)

    def facetSort(facet):
        sortBy = facet.get('sortBy', None)
        if sortBy is not None:
            if not sortBy in SolrInterface.SUPPORTED_SORTBY_VALUES:
                raise ValueError("'sortBy' should be one of %s" % SolrInterface.SUPPORTED_SORTBY_VALUES)
            arguments.setdefault('f.%s.facet.sort' % facet['fieldname'], []).append(sortBy)

    facets = facets or []
    joinFacets = joinFacets or []
    arguments = {}
    if facets or joinFacets:
        arguments['facet'] = "on"
        arguments['facet.mincount'] = "1"
        arguments['facet.field'] = []
        arguments['facet.pivot'] = []
        arguments['joinFacet.field'] = []
        for facet in facets:
            if isinstance(facet, dict):
                arguments['facet.field'].append(facet['fieldname'])
                facetLimit(facet)
                facetSort(facet)
            else:
                arguments["facet.pivot"].append(','.join(f['fieldname'] for f in facet))
                arguments['facet.pivot.mincount'] = "0"
                for f in facet:
                    facetLimit(f)
                    facetSort(f)
        for joinFacet in joinFacets:
            arguments['joinFacet.field'].append('{!facetjoin core=%(core)s from=%(fromField)s to=%(toField)s}%(facetField)s' % joinFacet)
    return arguments


def _updateResponseWithDrilldownData(arguments, facetCounts, response):
    drilldownData = []
    for fieldname, termCounts in facetCounts['facet_fields'].items():
        terms = []
        for i in xrange(0, len(termCounts), 2):
            terms.append({'term': termCounts[i], 'count': termCounts[i+1]})
        drilldownData.append(dict(fieldname=fieldname, terms=terms))
    if 'facet_pivot' in facetCounts:
        drilldownData.extend([_buildDrilldownDict(drilldown) \
                for drilldown in facetCounts['facet_pivot'].values() \
                    if drilldown])
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

