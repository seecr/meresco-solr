# -*- coding: utf-8 -*-
from unittest import main, TestCase
from StringIO import StringIO
from os import mkdir, listdir, system
from os.path import join, dirname, abspath, basename, isdir
from shutil import rmtree
from lxml.etree import parse
import sys

start_solr = __import__('start-solr')
mydir = dirname(abspath(__file__))
version = "3.6.0"

class SolrRunTest(TestCase):

    def testParseArguments(self):
        options, arguments = start_solr.parseArguments(['--port=8042', '--stateDir=/tmp', '--core=core1', '--core=core2'])
        self.assertEquals(8042, options.port)
        self.assertEquals('/tmp', options.stateDir)
        self.assertEquals(['core1', 'core2'], options.core)

    def testIncompleteArguments(self):
        stdout_mock = StringIO()
        sys.stdout = stdout_mock
        try:
            self.assertRaises(ValueError, lambda: start_solr.parseArguments(['--port=8042', '--stateDir=/tmp']))
        finally:
            sys.stdout = sys.__stdout__

    def testSetupSolrConfig(self):
        tempdir = "/tmp/testSetupSolrConfig"
        mkdir(tempdir)
        try:
            solrDataDir = join(tempdir, 'solr-data')
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, cores=['core1', 'córë2'])
            self.assertEquals(set(['contexts', 'cores', 'webdefault.xml', 'jetty.xml', 'start.config', 'solr.xml']), set(listdir(solrDataDir)))
            jetty_xml = parse(open(join(solrDataDir, 'jetty.xml')))
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
            self.assertEquals(['core1', 'córë2'], solr_xml.xpath("//core/@name"))
            self.assertEquals(['cores/core1', 'cores/córë2'], solr_xml.xpath("//core/@instanceDir"))

            schema_core1_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
            self.assertEquals(['meresco-core1'], schema_core1_xml.xpath("/schema/@name"))

            schema_core2_xml = parse(open(join(solrDataDir, 'cores', 'córë2', 'conf', 'schema.xml')))
            self.assertEquals(['meresco-córë2'], schema_core2_xml.xpath("/schema/@name"))
        finally:
            rmtree(tempdir)

    def testSetupSolrTwiceConfig(self):
        tempdir = "/tmp/testSetupSolrConfig"
        mkdir(tempdir)
        try:
            solrDataDir = join(tempdir, 'solr-data')
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, cores=['core1'])
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, cores=['core1', 'córë2'])
            self.assertEquals(set(['contexts', 'cores', 'webdefault.xml', 'jetty.xml', 'start.config', 'solr.xml']), set(listdir(solrDataDir)))
            jetty_xml = parse(open(join(solrDataDir, 'jetty.xml')))
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
            self.assertEquals(['core1', 'córë2'], solr_xml.xpath("//core/@name"))
            self.assertEquals(['cores/core1', 'cores/córë2'], solr_xml.xpath("//core/@instanceDir"))

            schema_core1_xml = parse(open(join(solrDataDir, 'cores', 'core1', 'conf', 'schema.xml')))
            self.assertEquals(['meresco-core1'], schema_core1_xml.xpath("/schema/@name"))

            schema_core2_xml = parse(open(join(solrDataDir, 'cores', 'córë2', 'conf', 'schema.xml')))
            self.assertEquals(['meresco-córë2'], schema_core2_xml.xpath("/schema/@name"))
        finally:
            rmtree(tempdir)

    def testNotMatchingLuceneMatchVersion(self):
        tempdir = "/tmp/testSetupSolrConfig"
        mkdir(tempdir)
        try:
            solrDataDir = join(tempdir, 'solr-data')
            start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, cores=['core1'])
            system('sed "s,<luceneMatchVersion>.*</luceneMatchVersion>,<luceneMatchVersion>LUCENE_32</luceneMatchVersion>," -i %s' % join(solrDataDir, 'cores', 'core1', 'conf', 'solrconfig.xml'))

            self.assertRaises(ValueError, lambda: start_solr.setupSolrConfig(stateDir=solrDataDir, port=8042, cores=['core1']))
        finally:
            rmtree(tempdir)


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

    def testStartSolrReally(self):
        tempdir = "/tmp/testSetupSolrConfig"
        isdir(tempdir) and rmtree(tempdir)
        mkdir(tempdir)
        solrDataDir = join(tempdir, 'solr-data')
        start_solr.setupSolrConfig(stateDir=solrDataDir, port=8000, cores=["test"])
        start_solr.startSolr(stateDir=solrDataDir, port=8000, javaMX="1024M")

if __name__ == '__main__':
    main()
