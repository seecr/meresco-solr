# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import dirname, abspath, join
from json import dumps

from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator


mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))

class ExistingIndexesState(_IntegrationState):
    def __init__(self, stateName, tests, indexes):
        _IntegrationState.__init__(self, "solr-"+stateName, tests=tests, fastMode=False)
        self.solrStates = {}
        for indexName, indexDict in indexes.items():
            self.solrStates[indexName] = _SolrState(
                    indexName,
                    indexDir=indexDict['dir'],
                    solrCore=indexDict['core'],
                    integrationTestDir=self.integrationTempdir,
                    stateName=self.stateName)

    def setUp(self):
        for solrState in self.solrStates.values():
            solrState.start(self)

    def binDir(self):
        return join(projectDir, 'bin')


class _SolrState(object):
    def __init__(self, name, indexDir, solrCore, integrationTestDir, stateName):
        self.name = name
        self.solrStatePath = indexDir
        self.solrPort = PortNumberGenerator.next()
        self.solrCore = solrCore
        self.config = {
                self.solrCore: {'autocomplete': True, 'suggestions': {'field': '__all__'}}
            }
        self.configPath = join(integrationTestDir, '%s.config' % self.name)
        with open(self.configPath, 'w') as f:
            f.write(dumps(self.config))

    def start(self, integrationstate):
        self._startSolrServer(integrationstate)

    def _startSolrServer(self, integrationstate):
        startSolrPath = integrationstate.binPath('start-solr')
        print 'startSolrPath', startSolrPath
        print
        from sys import stdout; stdout.flush()

        integrationstate._startServer(
                self.name,
                startSolrPath,
                'http://localhost:%s/solr/%s/admin/ping' % (self.solrPort, self.solrCore),
                port=self.solrPort,
                stateDir=self.solrStatePath,
                config=self.configPath)

