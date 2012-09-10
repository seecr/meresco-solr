#!/usr/bin/env python2.6
from sys import argv, exit
from os import execvp, system, makedirs, listdir
from os.path import dirname, abspath, isdir, join, isfile
from optparse import OptionParser, Option
from lxml.etree import parse, SubElement, tostring
from StringIO import StringIO
from subprocess import Popen

mydir = dirname(abspath(__file__))
configdir = join(dirname(mydir), 'usr-share') # is replaced by makeDeb.sh
SOLR_VERSION = "3.6.0"

def parseArguments(args):
    features = [f.rsplit('.', 1)[0] for f in listdir(join(configdir, 'solrconfig.d'))]
    parser = OptionParser(description="""Available features: %s.""" % ', '.join(features), epilog="""
Example config: 
{
    "core1": {},
    "core2": {"feature": {"option": "value"}},
    "core3": {"booleanFeature": true}
}
""")
    parser.format_epilog = lambda formatter: parser.epilog
    parser.add_option(Option('', '--port', type='int', help='Solr port number', dest='port'))
    parser.add_option(Option('', '--stateDir', type='string', help='Solr state directory', dest='stateDir'))
    parser.add_option(Option('', '--config', type='string', help="Filename with json configuration file for solr", dest="config"))
    parser.add_option(Option('', '--javaMX', type='string', help="Value for -Xmx setting for java", dest="javaMX", default="1024M"))
    options, arguments = parser.parse_args(args)
    if not all([options.port, options.stateDir, options.config]):
        parser.print_help()
        raise ValueError("Missing required option (all except javaMX are required)")
    return options, arguments

def copyDir(src, dst):
    system('cp -r %s/* %s/' % (src, dst))
    system('find %s -name ".svn" | xargs rm -rf' % dst) # DO_NOT_DISTRIBUTE

def setupSolrConfig(stateDir, port, config):
    assert all(type(v) == dict for v in config.values()), "Core feature descriptions must be a dictionary (empty for no additional features)."

    if not isdir(stateDir):
        makedirs(stateDir)
        copyDir(join(configdir, 'solr-data'), stateDir)
    else:
        newMatchVersion = parse(open(join(configdir, 'core-data', 'conf', 'solrconfig.xml'))).xpath("//luceneMatchVersion/text()")[0]
        for coreDir in listdir(join(stateDir, 'cores')):
            currentMatchVersion = parse(open(join(stateDir, 'cores', coreDir, 'conf', 'solrconfig.xml'))).xpath("//luceneMatchVersion/text()")[0]
            if currentMatchVersion != newMatchVersion:
                raise ValueError("LuceneMatchVersion in core '%s' does not match the new configuration. Remove the old index." % coreDir)

    _setupJettyXml(port, stateDir)
    _setupStartConfig(stateDir)
    _setupSolrXml(stateDir)
    _setupCoreData(stateDir, config.keys())

    for core, features in config.items():
        for feature, options in features.items():
            _setupFeature(name=feature, stateDir=stateDir, core=core, options=options)

def _setupFeature(name, stateDir, core, options):
    if options == False:
        return
    featureFilename = join(configdir, 'solrconfig.d', '%s.xml' % name)
    if not isfile(featureFilename):
        raise ValueError("Unknown feature '%s'" % name)

    feature = open(featureFilename).read()
    if type(options) is dict:
        feature = feature % options
    feature_xml = parse(StringIO(feature))
    solrconfig_file = join(stateDir, 'cores', core, 'conf', 'solrconfig.xml')
    core_sorlconfig = parse(open(solrconfig_file))
    core_sorlconfig.getroot().extend(feature_xml.xpath('/config/*'))
    open(solrconfig_file, 'w').write(tostring(core_sorlconfig, pretty_print=True, encoding="UTF-8"))

def _setupCoreData(stateDir, cores):
    solr_xml = parse(open(join(stateDir, 'solr.xml')))
    for core in cores:
        coreDir = join(stateDir, 'cores', core)
        if not isdir(coreDir):
            makedirs(coreDir)
            coresElement = solr_xml.xpath("/solr/cores")[0]
            SubElement(coresElement, "core", attrib={'name': unicode(core), 'instanceDir': join('cores', unicode(core))})
            copyDir(join(configdir, 'core-data'), coreDir)
            schema_xml_path = join(coreDir, 'conf', 'schema.xml')
            schema_xml = parse(open(schema_xml_path))
            schema_xml.xpath("/schema")[0].attrib['name'] = unicode("meresco-%s" % core)
            open(schema_xml_path, 'w').write(tostring(schema_xml, pretty_print=True, encoding="UTF-8"))

    open(join(stateDir, 'solr.xml'), 'w').write(tostring(solr_xml, pretty_print=True, encoding="UTF-8"))

def _setupJettyXml(port, stateDir):
    system(r"""sed 's,<SystemProperty name="jetty.port"[^/]*/>,<SystemProperty name="jetty.port" default="%s"/>,' -i %s""" % (
            port,
            join(stateDir, 'etc', 'jetty.xml')
        ))

def _setupStartConfig(stateDir):
    system(r"""sed 's,^jetty\.home=.*$,jetty.home=%s,' -i %s""" % (
            stateDir,
            join(stateDir, 'start.config')
        ))

    system(r"""sed 's,^/.*$,/usr/share/java/solr%s/*,' -i %s""" % (
            SOLR_VERSION,
            join(stateDir, 'start.config')
        ))

def _setupSolrXml(stateDir):
    system(r"""sed -e "s,<Set name=\"war\">.*</Set>,<Set name=\"war\">/usr/share/java/webapps/apache-solr-%s.war</Set>," -i %s/contexts/solr.xml""" % (SOLR_VERSION, stateDir))

def startSolr(stateDir, port, javaMX):
    _execvp('java', [
        'java',
        '-Xmx%s' % javaMX, 
        '-Djetty.port=%s' % port,
        '-DSTART=%s/start.config' % stateDir,
        '-Dsolr.solr.home=%s' % stateDir, 
        '-jar', '/usr/share/java/solr%s/start.jar' % SOLR_VERSION,
        ])

def _execvp(*args, **kwargs):
    execvp(*args, **kwargs)


if __name__ == '__main__':
    args = argv[1:]
    options, arguments = parseArguments(args)

    if Popen(["java -version 2>&1 | grep 'libgcj' > /dev/null 2>&1"], shell=True).wait() == 0:
        print "Don't use GCJ as the default java JRE."
        exit(1)

    setupSolrConfig(stateDir=options.stateDir, port=options.port, config=options.config)
    startSolr(stateDir=options.stateDir, port=options.port, javaMX=options.javaMX)

