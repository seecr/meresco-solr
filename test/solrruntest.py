# -*- coding: utf-8 -*-
## begin license ##
# 
# "Solr Run" starts Solr with correct parameters etc. 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# 
# This file is part of "Solr Run"
# 
# "Solr Run" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Solr Run" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Solr Run"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

import sys
from unittest import main
from StringIO import StringIO
from os import mkdir, listdir, system
from os.path import join, dirname, abspath, basename, isdir
from shutil import rmtree
from simplejson import dump as jsonDump
from lxml.etree import parse, tostring

from seecr.test import SeecrTestCase
start_solr = __import__('start-solr')


mydir = dirname(abspath(__file__))
version = "3.6.0"

class SolrRunTest(SeecrTestCase):
    def testParseArguments(self):
        options, arguments = start_solr.parseArguments(['--port=8042', '--stateDir=/tmp', '--config=/tmp/config.json'])
        self.assertEquals(8042, options.port)
        self.assertEquals('/tmp', options.stateDir)
        self.assertEquals('/tmp/config.json', options.config)

    def testIncompleteArguments(self):
        stdout_mock = StringIO()
        sys.stdout = stdout_mock
        try:
            self.assertRaises(ValueError, lambda: start_solr.parseArguments(['--port=8042', '--stateDir=/tmp']))
        finally:
            sys.stdout = sys.__stdout__

    def testSetupSolrConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
        self.assertEquals(set(['contexts', 'cores', 'start.config', 'solr.xml', 'etc']), set(listdir(solrDataDir)))
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
        self.assertTrue('/usr/share/java/solr3.6.0/*' in open(join(solrDataDir, 'start.config')).read())

        context_solr_xml = parse(open(join(solrDataDir, 'contexts', 'solr.xml')))
        self.assertEquals(['/usr/share/java/webapps/apache-solr-%s.war' % version], context_solr_xml.xpath('//Set[@name="war"]/text()'))

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
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}})
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
        self.assertEquals(set(['contexts', 'cores', 'start.config', 'solr.xml', 'etc']), set(listdir(solrDataDir)))
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
        self.assertTrue('/usr/share/java/solr3.6.0/*' in open(join(solrDataDir, 'start.config')).read())

        context_solr_xml = parse(open(join(solrDataDir, 'contexts', 'solr.xml')))
        self.assertEquals(['/usr/share/java/webapps/apache-solr-%s.war' % version], context_solr_xml.xpath('//Set[@name="war"]/text()'))

        self.assertEquals(set(['core1', 'córë2']), set(listdir(join(solrDataDir, 'cores'))))
        solr_xml = parse(open(join(solrDataDir, 'solr.xml')))
        self.assertEquals(set(['core1', u'córë2']), set(solr_xml.xpath("//core/@name")))
        self.assertEquals(set(['cores/core1', u'cores/córë2']), set(solr_xml.xpath("//core/@instanceDir")))

        schema_core1_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-core1'], schema_core1_xml.xpath("/schema/@name"))

        schema_core2_xml = parse(open(join(solrDataDir, 'cores', 'córë2', 'conf', 'schema.xml')))
        self.assertEquals(['meresco-córë2'], schema_core2_xml.xpath("/schema/@name"))

    def testSetupSolrConfigWithAutocomplete(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'autocomplete': {}}, 'core2': {}}
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertTrue('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertFalse('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertFalse('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

    def testSetupSolrConfigWithAdmin(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'admin': {}}, 'core2': {}}
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('/admin' in solrconfig_xml.xpath("/config/requestHandler/@name"))
        self.assertTrue('/admin/ping' in solrconfig_xml.xpath("/config/requestHandler/@name"))
        self.assertTrue('*:*' in solrconfig_xml.xpath("/config/admin/defaultQuery/text()"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertFalse('/admin' in solrconfig_xml.xpath("/config/requestHandler/@name"))
        self.assertFalse('/admin/ping' in solrconfig_xml.xpath("/config/requestHandler/@name"))
        self.assertFalse('*:*' in solrconfig_xml.xpath("/config/admin/defaultQuery/text()"))

    def testSetupSolrConfigWithSuggestions(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core2': {'suggestions': {'field': 'afieldname'}}, 'core1': {}}
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertEquals(['afieldname'], solrconfig_xml.xpath('/config/searchComponent[@name="suggestions"]/lst/str[@name="field"]/text()'))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))

    def testSetupSolrConfigWithAdditionalSolrConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        open(join(self.tempdir, 'solrconfig.xml'), 'w').write("""<config><extra>option</extra></config>""")
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core': {'additionalSolrConfig': join(self.tempdir, 'solrconfig.xml')}})
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core', 'conf', 'solrconfig.xml')))

        self.assertEquals(['option'], solrconfig_xml.xpath("/config/extra/text()"))

    def testSetupSolrConfigWithAdditionalInvalidSolrConfigShouldRaiseAnError(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        open(join(self.tempdir, 'solrconfig.xml'), 'w').write("""<extra>option</extra>""")
        try:
            self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core': {'additionalSolrConfig': join(self.tempdir, 'solrconfig.xml')}})
            self.fail()
        except ValueError, e:
            self.assertEquals("No elements found with which to extend the solrconfig.xml", str(e))

    def testSetupWithNoFeatures(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'suggestions': False}, 'core2': {}}
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))

    def testInvalidCoreConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'suggestions': False}, 'core2': False}
        try:
            self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except AssertionError, e:
            self.assertEquals("Core feature descriptions must be a dictionary (empty for no additional features).", str(e))
            self.assertFalse(isdir(solrDataDir))

    def testUnknownFeatureInConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'unknown-feature': True}}
        try:
            self._createSolrConfig(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except ValueError, e:
            self.assertEquals("Unknown feature 'unknown-feature'", str(e))

    def testNotMatchingLuceneMatchVersion(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}})
        system('sed "s,<luceneMatchVersion>.*</luceneMatchVersion>,<luceneMatchVersion>LUCENE_32</luceneMatchVersion>," -i %s' % join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml'))

        self.assertRaises(ValueError, lambda: self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}}))

    def testStartSolr(self):
        execCalled = []
        def execvpMock(*args, **kwargs):
            execCalled.append((args, kwargs))

        try:
            _original_execvp = start_solr._execvp
            start_solr._execvp = execvpMock
            solrConfig = self._createSolrConfig(stateDir=join(self.tempdir, 'the/state/dir'), port=1423, config={})
            solrConfig.start(javaMX="1234M")
            self.assertEquals(1, len(execCalled))
            self.assertEquals((
                'java', 
                ['java', '-Xmx1234M', '-Djetty.port=1423', '-DSTART=%s/the/state/dir/start.config' % self.tempdir, '-Dsolr.solr.home=%s/the/state/dir' % self.tempdir, '-jar', '/usr/share/java/solr3.6.0/start.jar'],
            ), execCalled[0][0])
            self.assertEquals({}, execCalled[0][1])
        finally:
            start_solr._execvp = _original_execvp

    def testSetupSolrCoreWithExtraFilters(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        self._createSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {'schemaExtension':[
            { 
                'extensionType': 'fieldTypeFilter',
                'fieldTypeName': 'text_ws',
                'filterClass': 'solr.ASCIIFoldingFilterFactory',
            }
        ]}})
        schemaXml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
        self.assertEquals(['solr.LowerCaseFilterFactory', 'solr.ASCIIFoldingFilterFactory'], schemaXml.xpath('/schema/types/fieldType[@name="text_ws"]/analyzer/filter/@class'))

    def xtestStartSolrReally(self):
        tempdir = "/tmp/testSetupSolrConfig"
        isdir(tempdir) and rmtree(tempdir)
        mkdir(tempdir)
        solrDataDir = join(tempdir, 'solr-data')
        solrConfig = self._createSolrConfig(stateDir=solrDataDir, port=8000, config={"test": {}})
        solrConfig.start(javaMX="1024M")

    def _createSolrConfig(self, stateDir, port, config):
        solrConfFile = join(self.tempdir, 'solr.conf')
        jsonDump(config, open(solrConfFile, 'w'))
        return start_solr.SolrConfig(stateDir, port, solrConfFile)
        

if __name__ == '__main__':
    main()
