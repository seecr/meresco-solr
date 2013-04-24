# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import join, abspath, dirname, basename
from time import sleep, time
from traceback import print_exc
from glob import glob
from simplejson import dumps

from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import postRequest

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))

class IntegrationState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "solr-"+stateName, tests=tests, fastMode=fastMode)

        self.testdataDir = join(dirname(mydir), 'data/integration')
        self.solrStatePath = join(self.integrationTempdir, 'solr')

        self.solrPort = PortNumberGenerator.next()
        self.solrClientPort = PortNumberGenerator.next()

        self.solrCore = "records"
        self.config = {
                self.solrCore: {
                    'autocomplete': True,
                    'suggestions': {'field': '__all__'},
                    'autoCommit': {'autoCommitMaxTime': 500}
                },
                'core2': {},
                'core3': {}
            }
        self.configPath = join(self.integrationTempdir, 'solr.config')
        with open(self.configPath, 'w') as f:
            f.write(dumps(self.config))

    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self._startMerescoSolrInterfaceServer()
        self._startSolrServer()
        self._createDatabase()

    def _startSolrServer(self):
        self._startServer('solr', self.binPath('start-solr'), 'http://localhost:%s/solr/%s/admin/ping' % (self.solrPort, self.solrCore), port=self.solrPort, stateDir=self.solrStatePath, config=self.configPath)

    def _startMerescoSolrInterfaceServer(self):
        self._startServer('solr-client', self.binPath('solrclientserver.py', binDirs=[mydir]), 'http://localhost:%s/ping' % self.solrClientPort, cwd=mydir, port=self.solrClientPort, solrPort=self.solrPort)

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        start = time()
        print "Creating database in", self.integrationTempdir
        try:
            self._uploadSolrData(join(self.testdataDir))
            sleep(5)
            print "Finished creating database in %s seconds" % (time() - start)
        except Exception, e:
            print 'Error received while creating database for', self.stateName
            print_exc()
            exit(1)

    def _uploadSolrData(self, dataDir):
        for docFile in sorted(glob(join(dataDir, '*.doc'))):
            # print docFile
            identifier = basename(docFile).rsplit('.',1)[0]
            addKwargs=dict(
                identifier=identifier,
                data=open(docFile).read(),
            )
            header, body = postRequest(port=self.solrClientPort, path='/add', data=dumps(addKwargs), parse=False)
            assert '' == body, 'Something bad happened:\n' + body


