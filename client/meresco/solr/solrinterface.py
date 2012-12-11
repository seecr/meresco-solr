## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from socket import socket
from lxml.etree import parse
from StringIO import StringIO
from time import sleep
from xml.sax.saxutils import escape as escapeXml
from weightless.http import httpget, httppost
from meresco.core import Observable

from solrresponse import SolrResponse

CRLF = '\r\n'

class SolrInterface(Observable):
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

    def add(self, identifier, partname, data):
        path = self._path('update')
        path += "?commitWithin=%d" % self._commitWithin
        yield self._send(path=path, body="<add>%s</add>" % data)

    def delete(self, identifier):
        path = self._path('update')
        path += "?commitWithin=%d" % self._commitWithin
        yield self._send(path=path, body="<delete><id>%s</id></delete>" % escapeXml(identifier))

    def executeQuery(self, luceneQueryString, start=0, stop=10, sortKeys=None, fieldnamesAndMaximums=None, suggestionsCount=0, suggestionsQuery=None, filterQuery=None, **kwargs):
        if not luceneQueryString:
            raise ValueError("Empty luceneQueryString not allowed.")
        arguments = dict(
                q=luceneQueryString, 
                start=start, 
                rows=stop-start, 
            )
        if sortKeys:
            arguments["sort"] = ','.join("%s %s" % (sortKey['sortBy'], 'desc' if sortKey['sortDescending'] else 'asc') for sortKey in sortKeys)
        if filterQuery:
            arguments['fq'] = filterQuery

        arguments.update(_drilldownArguments(fieldnamesAndMaximums))
        if suggestionsCount > 0 and suggestionsQuery:
            arguments["spellcheck"] = 'true'
            arguments["spellcheck.count"] = suggestionsCount
            arguments["spellcheck.q"] = suggestionsQuery

        path = self._path('select')
        body = yield self._send(path, urlencode(arguments, doseq=True), contentType='application/x-www-form-urlencoded')
        xml = parse(StringIO(body))
        recordCount = int(xml.xpath('/response/result/@numFound')[0])
        identifiers = xml.xpath('/response/result/doc/str[@name="__id__"]/text()')
        qtime = int(xml.xpath('/response/lst[@name="responseHeader"]/int[@name="QTime"]/text()')[0])
        response = SolrResponse(total=recordCount, hits=identifiers, queryTime=qtime)
        if fieldnamesAndMaximums is not None:
            _updateResponseWithDrilldownData(arguments, xml, response)
        if suggestionsCount > 0 and suggestionsQuery:
            _updateResponseWithSuggestionData(arguments, xml, response)
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


def _drilldownArguments(fieldnamesAndMaximums):
    arguments = {}
    if fieldnamesAndMaximums is not None:
        arguments['facet'] = "on"
        arguments['facet.mincount'] = "1"
        arguments['facet.field'] = []
        for fieldname, maximumResults, howToSort in fieldnamesAndMaximums:
            arguments['facet.field'].append(fieldname)
            arguments.setdefault('f.%s.facet.limit' % fieldname, []).append(-1 if maximumResults == 0 else maximumResults)
            arguments.setdefault('f.%s.facet.sort' % fieldname, []).append('count' if howToSort else 'index')
    return arguments

def _updateResponseWithDrilldownData(arguments, xml, response):
    drilldownData = []
    for facet_fields in xml.xpath('/response/lst[@name="facet_counts"]/lst[@name="facet_fields"]/lst'):
        drilldownResult = facet_fields.xpath('int')
        drilldownData.append((facet_fields.attrib["name"], ((termCount.attrib['name'], int(termCount.text)) for termCount in drilldownResult)))
    response.drilldownData = drilldownData

def _updateResponseWithSuggestionData(arguments, xml, response):
    suggestions = {}
    for suggestion in xml.xpath('/response/lst[@name="spellcheck"]/lst[@name="suggestions"]/lst'):
        startOffset = int(suggestion.xpath('int[@name="startOffset"]/text()')[0])
        endOffset = int(suggestion.xpath('int[@name="endOffset"]/text()')[0])
        suggestions[suggestion.attrib['name']] = (startOffset, endOffset, suggestion.xpath('arr[@name="suggestion"]/str/text()'))
    response.suggestions = suggestions