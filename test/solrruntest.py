# -*- coding: utf-8 -*-
from unittest import main
from seecr.test import SeecrTestCase
from StringIO import StringIO
from os import mkdir, listdir, system
from os.path import join, dirname, abspath, basename, isdir
from shutil import rmtree
from lxml.etree import parse
import sys

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
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
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
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}})
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}, 'córë2': {}})
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
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertTrue('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertTrue('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertFalse('terms' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertFalse('/terms' in solrconfig_xml.xpath("/config/requestHandler/@name"))

    def testSetupSolrConfigWithAdmin(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'admin': {}}, 'core2': {}}
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
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
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core2', 'conf', 'solrconfig.xml')))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertTrue('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))
        self.assertEquals(['afieldname'], solrconfig_xml.xpath('/config/searchComponent[@name="suggestions"]/lst/str[@name="field"]/text()'))

        solrconfig_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml')))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/requestHandler[@name='/select']/arr/str/text()"))
        self.assertFalse('suggestions' in solrconfig_xml.xpath("/config/searchComponent/@name"))

    def testSetupWithNoFeatures(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'suggestions': False}, 'core2': {}}
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
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
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except AssertionError, e:
            self.assertEquals("Core feature descriptions must be a dictionary (empty for no additional features).", str(e))
            self.assertFalse(isdir(solrDataDir))

    def testUnknownFeatureInConfig(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        config = {'core1': {'unknown-feature': True}}
        try:
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config=config)
            self.fail()
        except ValueError, e:
            self.assertEquals("Unknown feature 'unknown-feature'", str(e))

    def testNotMatchingLuceneMatchVersion(self):
        solrDataDir = join(self.tempdir, 'solr-data')
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}})
        system('sed "s,<luceneMatchVersion>.*</luceneMatchVersion>,<luceneMatchVersion>LUCENE_32</luceneMatchVersion>," -i %s' % join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml'))

        self.assertRaises(ValueError, lambda: start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, config={'core1': {}}))

    def testStartSolr(self):
        execCalled = []
        def execvpMock(*args, **kwargs):
            execCalled.append((args, kwargs))

        try:
            _original_execvp = start_solr._execvp
            start_solr._execvp = execvpMock
            start_solr.startSolr(stateDir='/the/state/dir', port=1423, javaMX="1234M")
            self.assertEquals(1, len(execCalled))
            self.assertEquals((
                'java', 
                ['java', '-Xmx1234M', '-Djetty.port=1423', '-DSTART=/the/state/dir/start.config', '-Dsolr.solr.home=/the/state/dir', '-jar', '/usr/share/java/solr3.6.0/start.jar'],
            ), execCalled[0][0])
            self.assertEquals({}, execCalled[0][1])
        finally:
            start_solr._execvp = _original_execvp

    def xxtestStartSolrReally(self):
        tempdir = "/tmp/testSetupSolrConfig"
        isdir(tempdir) and rmtree(tempdir)
        mkdir(tempdir)
        solrDataDir = join(tempdir, 'solr-data')
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8000, cores=["test"])
        start_solr.startSolr(stateDir=solrDataDir, port=8000, javaMX="1024M")

if __name__ == '__main__':
    main()
