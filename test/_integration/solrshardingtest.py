from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest

class SolrShardingTest(IntegrationTestCase):

    def testOne(self):
        header, body = getRequest(parse=False, 
                port=self.solr1.solrPort,
                path="/solr/records/select", 
                arguments= { "q": '*:*',
                    "rows": "2",
                    "shards": 'localhost:%s/solr/records,localhost:%s/solr/records' % (self.solr1.solrPort, self.solr2.solrPort),
                    "facet": 'on',
                    "facet.field": "untokenized.rdf:type"})
        print header, body
        raw_input("Ho! %s:" % self.solr2.solrPort)
