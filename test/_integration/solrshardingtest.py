from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest

class SolrShardingTest(IntegrationTestCase):

    def testSortingOnRelevancyWithShards(self):
        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select", 
                arguments= { "q": '__all__:fiets', 'fl': '__id__,score'})
        self.assertEquals(['record:0004', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['0.37158427', '0.18579213'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr2.solrPort,
                path="/solr/records/select", 
                arguments= { "q": '__all__:fiets', 'fl': '__id__,score'})
        self.assertEquals(['record:0003', 'record:0002'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['0.32180142', '0.26274976'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select", 
                arguments= { "q": '__all__:fiets',
                    "fl": "__id__,score",
                    "shards": 'localhost:%s/solr/records,localhost:%s/solr/records' % (self.solr1.solrPort, self.solr2.solrPort)})
        self.assertEquals(['record:0004', 'record:0003', 'record:0002', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))
