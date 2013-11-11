## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os import makedirs, listdir, system, execvp
from os.path import dirname, abspath, isdir, isfile, join
from shutil import copytree, rmtree
from re import compile, MULTILINE
from StringIO import StringIO
from lxml.etree import parse, SubElement, tostring
from simplejson import load as jsonLoad


mydir = dirname(abspath(__file__))
usrShareDir = '/usr/share/meresco-solr'
usrShareDir = join(dirname(dirname(mydir)), 'usr-share') # DO_NOT_DISTRIBUTE
SOLR_VERSION = "4.5.1"


class Server(object):
    def __init__(self, stateDir, port, configFile):
        self.config=jsonLoad(open(configFile))
        self.stateDir = stateDir
        self.port = port
        self.configBasedir = dirname(abspath(configFile))
        assert all(type(v) == dict for v in self.config.values()), "Core feature descriptions must be a dictionary (empty for no additional features)."

        if not isdir(self.stateDir):
            copytree(join(usrShareDir, 'solr-data'), self.stateDir)
        else:
            newMatchVersion = parse(open(join(usrShareDir, 'core-data', 'conf', 'solrconfig.xml'))).xpath("//luceneMatchVersion/text()")[0]
            for coreDir in listdir(join(self.stateDir, 'cores')):
                currentMatchVersion = parse(open(join(self.stateDir, 'cores', coreDir, 'conf', 'solrconfig.xml'))).xpath("//luceneMatchVersion/text()")[0]
                if currentMatchVersion != newMatchVersion:
                    raise ValueError("LuceneMatchVersion in core '%s' does not match the new configuration. Remove the old index." % coreDir)
            rmtree(join(self.stateDir, 'lib'))
            copytree(join(usrShareDir, 'solr-data', 'lib'), join(self.stateDir, 'lib'))

        self._setupJettyXml()
        self._setupStartConfig()
        self._setupSolrXml()
        self._setupCoreData()

        self._setFeatureDefaults('autoCommit', {'autoCommitMaxTime': 1000})
        for core, features in self.config.items():
            for feature, options in features.items():
                self._setupFeature(name=feature, core=core, options=options)

    def _setFeatureDefaults(self, featureName, defaultOptions):
        for core, features in self.config.items():
            feature = features.setdefault(featureName, {})
            for key, value in defaultOptions.items():
                if not key in feature:
                    feature[key] = value

    def _setupFeature(self, name, core, options):
        if name == 'additionalSolrConfig':
            filepath = options if options.startswith('/') else join(self.configBasedir, options)
            self._extendSolrConfig(core=core, lxmlElementList=parse(open(filepath)).xpath('/config/*'))
            return
        if name == 'additionalSchemaXml':
            filepath = options if options.startswith('/') else join(self.configBasedir, options)
            self._extendSchemaXml(core=core, lxmlElementList=parse(open(filepath)).xpath('/schema/*'))
            return
        if options == False:
            return
        featureFilename = join(usrShareDir, 'solrconfig.d', '%s.xml' % name)
        if not isfile(featureFilename):
            raise ValueError("Unknown feature '%s'" % name)

        feature = open(featureFilename).read()
        if type(options) is dict:
            feature = feature % options
        feature_xml = parse(StringIO(feature))
        self._extendSolrConfig(core=core, lxmlElementList=feature_xml.xpath('/config/*'))

    def _extendSolrConfig(self, core, lxmlElementList):
        if not lxmlElementList:
            raise ValueError("No elements found with which to extend the solrconfig.xml")
        solrconfig_file = join(self.stateDir, 'cores', core, 'conf', 'solrconfig.xml')
        core_sorlconfig = parse(open(solrconfig_file))
        core_sorlconfig.getroot().extend(lxmlElementList)
        open(solrconfig_file, 'w').write(tostring(core_sorlconfig, pretty_print=True, encoding="UTF-8"))

    def _extendSchemaXml(self, core, lxmlElementList):
        if not lxmlElementList:
            raise ValueError("No elements found with which to extend the schema.xml")
        schemaxml_file = join(self.stateDir, 'cores', core, 'conf', 'schema.xml')
        core_sorlconfig = parse(open(schemaxml_file))
        core_sorlconfig.getroot().extend(lxmlElementList)
        open(schemaxml_file, 'w').write(tostring(core_sorlconfig, pretty_print=True, encoding="UTF-8"))

    def _setupCoreData(self):
        cores = self.config.keys()
        solr_xml = parse(open(join(self.stateDir, 'solr.xml')))
        coresElement = solr_xml.xpath("/solr/cores")[0]
        [coresElement.remove(child) for child in coresElement.getchildren()]
        for core in cores:
            SubElement(coresElement, "core", attrib={'name': unicode(core), 'instanceDir': join('cores', unicode(core))})
            coreDir = join(self.stateDir, 'cores', core)
            if not isdir(coreDir):
                makedirs(coreDir)
            confDir = join(coreDir, 'conf')
            isdir(confDir) and rmtree(confDir)
            copytree(join(usrShareDir, 'core-data', 'conf'), confDir)
            schema_xml_path = join(coreDir, 'conf', 'schema.xml')
            schema_xml = parse(open(schema_xml_path))
            schema_xml.xpath("/schema")[0].attrib['name'] = unicode("meresco-%s" % core)
            open(schema_xml_path, 'w').write(tostring(schema_xml, pretty_print=True, encoding="UTF-8"))

        open(join(self.stateDir, 'solr.xml'), 'w').write(tostring(solr_xml, pretty_print=True, encoding="UTF-8"))

    def _setupJettyXml(self):
        system(r"""sed 's,<SystemProperty name="jetty.port"[^/]*/>,<SystemProperty name="jetty.port" default="%s"/>,' -i %s""" % (
                self.port,
                join(self.stateDir, 'etc', 'jetty.xml')
            ))

    def _setupStartConfig(self):
        startConfigPath = join(self.stateDir, 'start.config')
        startConfig = open(startConfigPath).read()
        startConfig = compile('^jetty\.home=.*$', flags=MULTILINE).sub('jetty.home=' + self.stateDir, startConfig)
        startConfig = compile('^jetty\.lib=.*$', flags=MULTILINE).sub('jetty.lib=/usr/share/java/solr%s' % SOLR_VERSION, startConfig)
        open(startConfigPath, 'w').write(startConfig)

    def _setupSolrXml(self):
        system(r"""sed -e "s,<Set name=\"war\">.*</Set>,<Set name=\"war\">/usr/share/java/webapps/solr-%s.war</Set>," -i %s/contexts/solr.xml""" % (SOLR_VERSION, self.stateDir))

    def start(self, javaMX):
        self._execvp(
            'java', [
                'java',
                '-Xmx%s' % javaMX,
                '-Djetty.port=%s' % self.port,
                '-DSTART=%s/start.config' % self.stateDir,
                '-Dsolr.solr.home=%s' % self.stateDir,
                '-jar', '/usr/share/java/solr%s/start.jar' % SOLR_VERSION,
            ])

    def _execvp(self, *args, **kwargs):
        execvp(*args, **kwargs)
