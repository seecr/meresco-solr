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

from urllib import urlencode
from socket import socket
from lxml.etree import parse
from StringIO import StringIO
from time import sleep
from xml.sax.saxutils import escape as escapeXml
from weightless.http import httpget, httppost
from meresco.components.facetindex import Response

class SolrInterface(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def unknown(self, message, *args, **kwargs):
        print 'Unexpected unknown for:', message, args, kwargs

    def docsetFromQuery(self, *args, **kwargs):
        return None

    def add(self, identifier, partname, data):
        yield self._send(path='/solr/openindex/update', text="<add>%s</add>" % data)
        yield self._send(path='/solr/openindex/update', text="<commit/>")

    def delete(self, identifier):
        yield self._send(path='/solr/openindex/update', text="<delete><id>%s</id></delete>" % escapeXml(identifier))
        yield self._send(path='/solr/openindex/update', text='<commit expungeDeletes="true"/>')

    def executeQuery(self, luceneQueryString, start=0, stop=10, sortBy=None, sortDescending=None, fieldnamesAndMaximums=None, **kwargs):
        arguments = dict(
                q=luceneQueryString, 
                start=start, 
                rows=stop-start, 
            )
        if sortBy is not None:
            arguments["sort"] = "%s %s" % (sortBy, 'desc' if sortDescending else 'asc')
        arguments.update(_drilldownArguments(fieldnamesAndMaximums))

        body = yield self._read('/solr/openindex/select?%s' % (urlencode(arguments, doseq=True)))
        xml = parse(StringIO(body))
        recordCount = int(xml.xpath('/response/result/@numFound')[0])
        identifiers = xml.xpath('/response/result/doc/str[@name="__id__"]/text()')
        response = Response(total=recordCount, hits=identifiers)
        if fieldnamesAndMaximums is not None:
            _updateResponseWithDrilldownData(arguments, xml, response)
        raise StopIteration(response)

    def _send(self, path, text):
        response = yield httppost(self._host, self._port, path, text, headers={'Content-Type': 'text/xml', 'Content-Length': len(text)})
        raise StopIteration(response)

    def _read(self, path):
        response = yield httpget(self._host, self._port, path)
        header, body = response.split('\r\n\r\n', 1)
        raise StopIteration(body)

def _drilldownArguments(fieldnamesAndMaximums):
    arguments = {}
    if fieldnamesAndMaximums is not None:
        arguments['facet'] = "on"
        arguments['facet.mincount'] = "1"
        arguments['facet.field'] = []
        for fieldname, maximumResults, howToSort in fieldnamesAndMaximums:
            arguments['facet.field'].append(fieldname)
            arguments['f.%s.facet.limit' % fieldname] = -1 if maximumResults == 0 else maximumResults
            arguments['f.%s.facet.sort' % fieldname] = 'count' if howToSort else 'index'
    return arguments

def _updateResponseWithDrilldownData(arguments, xml, response):
    drilldownData = []
    for fieldname in arguments['facet.field']:
        drilldownResult = xml.xpath('/response/lst[@name="facet_counts"]/lst[@name="facet_fields"]/lst[@name="%s"]/int' % fieldname)
        drilldownData.append((fieldname, ((termCount.attrib['name'], int(termCount.text)) for termCount in drilldownResult)))
    response.drilldownData = drilldownData
