# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2013 Stichting Kennisnet http://www.kennisnet.nl
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

from os import mkdir, listdir, system, makedirs
from os.path import join, dirname, abspath, isdir
from shutil import rmtree
from simplejson import dump as jsonDump
from lxml.etree import parse

from meresco.solr.server import Server

from seecr.test import SeecrTestCase

mydir = dirname(abspath(__file__))
version = "4.5.1"

class ServerTest(SeecrTestCase):
    def testSetupSolrConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createServer(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
        self.assertEquals(set(['lib', 'contexts', 'cores', 'start.config', 'solr.xml', 'etc', 'resources']), set(listdir(solrDataDir)))
        self.assertEquals(set(['webdefault.xml', 'jetty.xml']), set(listdir(join(solrDataDir, 'etc'))))
        jetty_xml = parse(open(join(solrDataDir, 'etc', 'jetty.xml')))
        self.assertEquals(['8042'], jetty_xml.xpath('//SystemProperty[@name="jetty.port"]/@default'))

        f = open(join(solrDataDir, 'start.config'))
        for line in f:
            if line.startswith('jetty.home'):
                break
        else:
            self.fail("No jetty.home line found")
        f.close()
        self.assertEquals('jetty.home=%s\n' % solrDataDir, line)
        self.assertTrue('jetty.lib=/usr/share/java/solr4.5.1' in open(join(solrDataDir, 'start.config')).read())

        context_solr_xml = parse(open(join(solrDataDir, 'contexts', 'solr.xml')))
        self.assertEquals(['/usr/share/java/webapps/solr-%s.war' % version], context_solr_xml.xpath('//Set[@name="war"]/text()'))

        self.assertEquals(set(['core1', 'córë2']), set(listdir(join(solrDataDir, 'cores'))))
        solr_xml = parse(open(join(solrDataDir, 'solr.xml')))
        self.assertEquals(set([u'córë2', 'core1']), set(solr_xml.xpath("//core/@name")))
        self.assertEquals(set(['cores/core1', u'cores/córë2']), set(solr_xml.xpath("//core/@instanceDir")))

        schema_core1_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-core1'], schema_core1_xml.xpath("/schema/@name"))

        schema_core2_xml = parse(open(join(solrDataDir, 'cores', 'córë2', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-córë2'], schema_core2_xml.xpath("/schema/@name"))

    def testSetupSolrTwiceConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createServer(stateDir=solrDataDir, port=8042, config={'core1': {}})
        makedirs(join(solrDataDir, 'cores', 'core1', 'data'))
        self.assertEquals(set(['data', 'conf']), set(listdir(join(solrDataDir, 'cores', 'core1'))))
        self._createServer(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
        self.assertEquals(set(['lib', 'contexts', 'cores', 'start.config', 'solr.xml', 'etc', 'resources']), set(listdir(solrDataDir)))
        self.assertEquals(set(['webdefault.xml', 'jetty.xml']), set(listdir(join(solrDataDir, 'etc'))))
        jetty_xml = parse(open(join(solrDataDir, 'etc', 'jetty.xml')))
        self.assertEquals(['8042'], jetty_xml.xpath('//SystemProperty[@name="jetty.port"]/@default'))

        f = open(join(solrDataDir, 'start.config'))
        for line in f:
            if line.startswith('jetty.home'):
                break
        else:
            self.fail("No jetty.home line found")
        f.close()
        self.assertEquals('jetty.home=%s\n' % solrDataDir, line)
        self.assertTrue('jetty.lib=/usr/share/java/solr4.5.1' in open(join(solrDataDir, 'start.config')).read())

        context_solr_xml = parse(open(join(solrDataDir, 'contexts', 'solr.xml')))
        self.assertEquals(['/usr/share/java/webapps/solr-%s.war' % version], context_solr_xml.xpath('//Set[@name="war"]/text()'))

        self.assertEquals(set(['core1', 'córë2']), set(listdir(join(solrDataDir, 'cores'))))
        solr_xml = parse(open(join(solrDataDir, 'solr.xml')))
        self.assertEquals(set(['core1', u'córë2']), set(solr_xml.xpath("//core/@name")))
        self.assertEquals(set(['cores/core1', u'cores/córë2']), set(solr_xml.xpath("//core/@instanceDir")))

        schema_core1_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-core1'], schema_core1_xml.xpath("/schema/@name"))

        schema_core2_xml = parse(open(join(solrDataDir, 'cores', 'córë2', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-córë2'], schema_core2_xml.xpath("/schema/@name"))

        self.assertEquals(set(['data', 'conf']), set(listdir(join(solrDataDir, 'cores', 'core1'))))

    def testSetupSolrConfigWithAutocomplete(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'autocomplete': {}}, 'core2': {}}
        self._createServer(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertTrue('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertFalse('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertFalse('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

    def testSetupSolrConfigWithSuggestions(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core2': {'suggestions': {'field': 'afieldname'}}, 'core1': {}}
        self._createServer(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertTrue('textSpell' in solrconfig_xml.xpath("/config/searchComponent/str/text()"))
        self.assertEquals(['afieldname'], solrconfig_xml.xpath('/config/searchComponent[@name="suggestions"]/lst/str[@name="field"]/text()'))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('textSpell' in solrconfig_xml.xpath("/config/searchComponent/str/text()"))

    def testSetupSolrConfigWithAdditionalSolrConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        open(join(self.tempdir, 'solrconfig.xml'), 'w').write("""<config><extra>option</extra></config>""")
        self._createServer(stateDir=solrDataDir, port=8042, config={'core': {'additionalSolrConfig': join(self.tempdir, 'solrconfig.xml')}})
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core', 'conf', 'solrconfig.xml')))

        self.assertEquals(['option'], solrconfig_xml.xpath("/config/extra/text()"))

    def testSetupSolrConfigWithAdditionalSchemaXml(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        open(join(self.tempdir, 'schema.xml'), 'w').write("""<schema><fields><field name="extra"/></fields></schema>""")
        self._createServer(stateDir=solrDataDir, port=8042, config={'core': {'additionalSchemaXml': join(self.tempdir, 'schema.xml')}})
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core', 'conf', 'schema.xml')))

        self.assertEquals(1, len(solrconfig_xml.xpath("/schema/fields/field[@name='extra']")))

    def testSetupSolrConfigWithAdditionalInvalidSolrConfigShouldRaiseAnError(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        open(join(self.tempdir, 'solrconfig.xml'), 'w').write("""<extra>option</extra>""")
        try:
            self._createServer(stateDir=solrDataDir, port=8042, config={'core': {'additionalSolrConfig': join(self.tempdir, 'solrconfig.xml')}})
            self.fail()
        except ValueError, e:
            self.assertEquals("No elements found with which to extend the solrconfig.xml", str(e))

    def testSetupWithNoFeatures(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'suggestions': False}, 'core2': {}}
        self._createServer(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('textSpell' in solrconfig_xml.xpath("/config/searchComponent/str/text()"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('textSpell' in solrconfig_xml.xpath("/config/searchComponent/str/text()"))

    def testInvalidCoreConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'suggestions': False}, 'core2': False}
        try:
            self._createServer(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except AssertionError, e:
            self.assertEquals("Core feature descriptions must be a dictionary (empty for no additional features).", str(e))
            self.assertFalse(isdir(solrDataDir))

    def testUnknownFeatureInConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'unknown-feature': True}}
        try:
            self._createServer(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except ValueError, e:
            self.assertEquals("Unknown feature 'unknown-feature'", str(e))

    def testNotMatchingLuceneMatchVersion(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createServer(stateDir=solrDataDir, port=8042, config={'core1': {}})
        system('sed "s,<luceneMatchVersion>.*</luceneMatchVersion>,<luceneMatchVersion>LUCENE_32</luceneMatchVersion>," -i %s' % join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml'))

        self.assertRaises(ValueError, lambda: self._createServer(stateDir=solrDataDir, port=8042, config={'core1': {}}))

    def testStartSolr(self):
        solrServer = self._createServer(stateDir=join(self.tempdir, 'the/state/dir'), port=1423, config={})
        execCalled = []
        solrServer._execvp = lambda *args, **kwargs: execCalled.append((args, kwargs))
        solrServer.start(javaMX="1234M")
        self.assertEquals(1, len(execCalled))
        self.assertEquals((
            'java',
            ['java', '-Xmx1234M', '-Djetty.port=1423', '-DSTART=%s/the/state/dir/start.config' % self.tempdir, '-Dsolr.solr.home=%s/the/state/dir' % self.tempdir, '-jar', '/usr/share/java/solr4.5.1/start.jar'],
        ), execCalled[0][0])
        self.assertEquals({}, execCalled[0][1])

    def xtestStartSolrReally(self):
        tempdir = "/tmp/testSetupSolrConfig"
        isdir(tempdir) and rmtree(tempdir)
        mkdir(tempdir)
        solrDataDir = join(tempdir, 'solr-data')
        solrServer = self._createServer(stateDir=solrDataDir, port=8000, config={"test": {'admin': True}})
        solrServer.start(javaMX="1024M")

    def _createServer(self, stateDir, port, config):
        solrConfFile = join(self.tempdir, 'solr.conf')
        jsonDump(config, open(solrConfFile, 'w'))
        return Server(stateDir, port, solrConfFile)


