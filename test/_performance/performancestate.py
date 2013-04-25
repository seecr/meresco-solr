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

from os.path import join, dirname, abspath
from time import time
from traceback import print_exc

from simplejson import dumps

from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import postRequest, sleepWheel


mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))


class PerformanceState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "solr-"+stateName, tests=tests, fastMode=fastMode)

        self.solrStatePath = join(self.integrationTempdir, 'solr')

        self.solrPort = PortNumberGenerator.next()

        self.solrCore = "core1"
        self.config = {
                self.solrCore: {},
                'core2': {},
                'core3': {}
            }
        self.configPath = join(self.integrationTempdir, 'solr.config')
        with open(self.configPath, 'w') as f:
            f.write(dumps(self.config))

    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self._startSolrServer()
        self._createDatabase()

    def _startSolrServer(self):
        self._startServer('solr', self.binPath('start-solr'), 'http://localhost:%s/solr/%s/admin/ping' % (self.solrPort, self.solrCore), port=self.solrPort, stateDir=self.solrStatePath, config=self.configPath, javaMX='2048M')

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        start = time()
        print "Creating database in", self.integrationTempdir
        try:
            self._uploadSolrData()
            sleepWheel(5)
            print "Finished creating database in %s seconds" % (time() - start)
        except Exception:
            print 'Error received while creating database for', self.stateName
            print_exc()
            exit(1)

    def _uploadSolrData(self):
        BIGNUM = 1000000
        print 'uploading data to core1'
        for i in xrange(BIGNUM):
            if i % 1000 == 0:
                print i
            id = 'id%s' % i
            self.postToCore('core1', [('__id__', id), ('joinhash.__id__', hash(id)), ('field1', 'value')])

        print 'uploading data to core2'
        for i in xrange(0, BIGNUM, 3):
            if i % 1000 == 0:
                print i
            id = 'id%s' % i
            self.postToCore('core2', [('__id__', id), ('joinhash.__id__', hash(id)), ('field2', 'value%s' % (i % 5))])

        print 'uploading data to core3'
        for i in xrange(0, BIGNUM, 7):
            if i % 1000 == 0:
                print i
            id = 'id%s' % i
            self.postToCore('core3', [('__id__', id), ('joinhash.__id__', hash(id)), ('field3', 'value')])


    def postToCore(self, core, fields):
        postRequest(port=self.solrPort, 
            path='/solr/%s/update' % core, 
            data="""<add xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><doc>%s</doc></add>""" % ''.join('<field name="%s">%s</field>' % (f, v) for f, v in fields),
            contentType='text/xml')
