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

        self.testdataDir = join(dirname(mydir), 'data/integration')
        self.solrStatePath = join(self.integrationTempdir, 'solr')

        self.solrPort = PortNumberGenerator.next()

        self.solrCore = "records"
        self.config = {
                self.solrCore: {}
            }
        self.configPath = join(self.integrationTempdir, 'solr.config')
        with open(self.configPath, 'w') as f:
            f.write(dumps(self.config))

    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self._startSolrServer()
        self._createDatabase()
   
    def tearDown(self):
        _IntegrationState.tearDown(self)

    def _startSolrServer(self):
        self._startServer('solr', self.binPath('start-solr'), 'http://localhost:%s/solr/%s/admin/ping' % (self.solrPort, self.solrCore), port=self.solrPort, stateDir=self.solrStatePath, config=self.configPath)

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        start = time()
        print "Creating database in", self.integrationTempdir
        try:
            self._uploadSolrData(join(self.testdataDir))
            print "Finished creating database in %s seconds" % (time() - start)
        except Exception, e:
            print 'Error received while creating database for', self.stateName
            print_exc()
            exit(1)

    def _uploadSolrData(self, dataDir):
        for f in sorted(glob(join(dataDir, 'solr*.records'))):
            print 'HIER VERDER'
            break
            oaibatchLxml = parse(open(f))
            for record in xpath(oaibatchLxml, '//oai:record'):
                print 'Uploading %s' % xpath(record, 'oai:header/oai:identifier/text()')[0]
                data = lxmltostring(xpath(record, 'oai:metadata/doc')[0])
                postRequest(port=self.solrPort, path='/solr/%s/update' % self.solrCore, data='<add>%s</add>' % data, contentType='text/xml')
                postRequest(port=self.solrPort, path='/solr/%s/update' % self.solrCore, data='<commit/>', contentType='text/xml')
        

