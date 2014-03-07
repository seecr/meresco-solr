#!/usr/bin/env python
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

import sys                # DO_NOT_DISTRIBUTE
sys.path.insert(0, '../..')  # DO_NOT_DISTRIBUTE

from meresco.core import Observable

from weightless.core import be, compose
from weightless.io import Reactor
from simplejson import loads, dumps

from meresco.components.http.utils import okPlainText
from meresco.components.http import ObservableHttpServer
from meresco.components import ParseArguments

from meresco.solr import SolrInterface
from traceback import format_exc


class _HelperHandler(Observable):
    def handleRequest(self, path, Body, **kwargs):
        if path == '/ping':
            yield okPlainText
            yield 'pong'
            return
        methodKwargs = loads(Body)
        message = [p for p in path.split('/') if p][0]
        yield okPlainText
        try:
            if message in ['add', 'delete']:
                yield self.all.unknown(message, **methodKwargs)
            else:
                response = yield self.any.unknown(message, **methodKwargs)
                d = vars(response)
                print d
                from sys import stdout; stdout.flush()
                d['hits'] = [getattr(hit, 'id', hit) for hit in d['hits']]
                yield "%s: %s" % (type(response).__name__, dumps(d))
        except:
            yield format_exc()

def createServer(reactor, port, solrPort):
    return be((Observable(),
        (ObservableHttpServer(reactor, port),
            (_HelperHandler(),
                (SolrInterface(host='localhost', port=solrPort, core='records'),)
            )
        )
    ))

def main():
    parser = ParseArguments()
    parser.addOption('', '--port', type='int', mandatory=True)
    parser.addOption('', '--solrPort', type='int', mandatory=True)
    options, arguments = parser.parse()

    reactor = Reactor()
    server = createServer(reactor, **vars(options))
    list(compose(server.once.observer_init()))
    reactor.loop()

if __name__ == '__main__':
    main()
