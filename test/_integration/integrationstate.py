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

from os.path import isdir, join, abspath, dirname, basename, isfile
from os import makedirs
from sys import path as systemPath
from time import sleep, time 
from traceback import print_exc
from uuid import uuid4
from simplejson import dump
from glob import glob
from xml.sax.saxutils import escape as xmlEscape
from escaping import unescapeFilename
from lxml.etree import parse
from meresco.components import lxmltostring
from urllib import urlopen
from shutil import copyfile
from simplejson import dumps

from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import postRequest, sleepWheel

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))

class IntegrationState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "solr-"+stateName, tests=tests, fastMode=fastMode)
        self.solr1 = SolrState("solr1", integrationTestDir=self.integrationTempdir)
        self.solr2 = SolrState("solr2", integrationTestDir=self.integrationTempdir)

    def setUp(self):
        self.solr1.start(self)
        self.solr2.start(self)
        self._createDatabase()

    def binDir(self):
        return join(projectDir, 'bin')

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        start = time()
        print "Creating database in", self.integrationTempdir
        try:
            self.solr1._uploadSolrData()
            self.solr2._uploadSolrData()
            sleep(5)
            print "Finished creating database in %s seconds" % (time() - start)
        except Exception, e:
            print 'Error received while creating database for', self.stateName
            print_exc()
            exit(1)


class SolrState(object):
    def __init__(self, stateName, integrationTestDir):
        self.stateName = stateName
        self.testdataDir = join(dirname(mydir), 'data/integration')
        self.solrStatePath = join(integrationTestDir, self.stateName)
        self.solrPort = PortNumberGenerator.next()
        self.solrClientPort = PortNumberGenerator.next()
        self.solrCore = "records"
        self.config = {
                self.solrCore: {'autocomplete': True, 'suggestions': {'field': '__all__'}}
            }
        self.configPath = join(integrationTestDir, '%s.config' % self.stateName)
        with open(self.configPath, 'w') as f:
            f.write(dumps(self.config))

    def start(self, integrationstate):
        self._startSolrServer(integrationstate)
        self._startMerescoSolrInterfaceServer(integrationstate)
   
    def _startSolrServer(self, integrationstate):
        integrationstate._startServer(
                self.stateName,
                integrationstate.binPath('start-solr'),
                'http://localhost:%s/solr/%s/admin/ping' % (self.solrPort, self.solrCore),
                port=self.solrPort,
                stateDir=self.solrStatePath,
                config=self.configPath)

    def _startMerescoSolrInterfaceServer(self, integrationstate):
        integrationstate._startServer(
                self.stateName + 'client',
                integrationstate.binPath('solrclientserver.py', binDirs=[mydir]),
                'http://localhost:%s/ping' % self.solrClientPort,
                cwd=mydir,
                port=self.solrClientPort,
                solrPort=self.solrPort)

    def _uploadSolrData(self):
        for docFile in sorted(glob(join(self.testdataDir, '*.doc'))):
            # print docFile
            identifier = basename(docFile).rsplit('.',1)[0]
            addKwargs=dict(
                identifier=identifier,
                data=open(docFile).read(),
            )
            header, body = postRequest(port=self.solrClientPort, path='/add', data=dumps(addKwargs), parse=False)
            assert '' == body, 'Something bad happened:\n' + body
               

