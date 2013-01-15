from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest

class SolrShardingTest(IntegrationTestCase):

    def keepForLater_testSortingOnRelevancyWithShards(self):
        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'fiets', 'fl': '__id__,score', "debugQuery": "on"})
        self.assertEquals(set(['record:0004', 'record:0001']), set(body.xpath('//doc/str[@name="__id__"]/text()')))
        # self.assertEquals(['0.37158427', '0.18579213'], body.xpath('//doc/float[@name="score"]/text()'))
        self.assertEquals(['1.0', '1.0'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr2.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'fiets', 'fl': '__id__,score'})
        self.assertEquals(['record:0003', 'record:0002'], body.xpath('//doc/str[@name="__id__"]/text()'))
        # self.assertEquals(['0.32180142', '0.26274976'], body.xpath('//doc/float[@name="score"]/text()'))
        self.assertEquals(['0.19132218', '0.15621391'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'fiets',
                    "fl": "__id__,score",
                    "shards": 'localhost:%s/solr/records,localhost:%s/solr/records' % (self.solr1.solrPort, self.solr2.solrPort)})
        self.assertEquals(['record:0004', 'record:0003', 'record:0002', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))

    def testSortingOnRelevancyWithORquery(self):
        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score'})
        self.assertEquals(['record:0004', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['1.0', '0.25'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr2.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score'})
        self.assertEquals(['record:0003', 'record:0002'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['0.75', '0.5'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr2.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score',
                    "shards": 'localhost:%s/solr/records,localhost:%s/solr/records' % (self.solr1.solrPort, self.solr2.solrPort)})
        self.assertEquals(['record:0004', 'record:0003', 'record:0002', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))
        # self.assertEquals(['0.57226515', '0.18706693', '0.051650114', '0.0150798615'], body.xpath('//doc/float[@name="score"]/text()'))
        self.assertEquals(['1.0', '0.75', '0.5', '0.25'], body.xpath('//doc/float[@name="score"]/text()'))

    def testTryToGetScoresOnCoordinationFactorOnlyAndNotTFIDF(self):
        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score'})
        self.assertEquals(['record:0004', 'record:0001'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['1.0', '0.25'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr2.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score'})
        self.assertEquals(['record:0003', 'record:0002'], body.xpath('//doc/str[@name="__id__"]/text()'))
        self.assertEquals(['0.75', '0.5'], body.xpath('//doc/float[@name="score"]/text()'))

        header, body = getRequest(port=self.solr1.solrPort,
                path="/solr/records/select",
                arguments= { "q": 'zadel OR stuur OR wiel OR ketting', 'fl': '__id__,score',
                    "shards": 'localhost:%s/solr/records,localhost:%s/solr/records' % (self.solr1.solrPort, self.solr2.solrPort)})
        self.assertEquals(['1.0', '0.75', '0.5', '0.25'], body.xpath('//doc/float[@name="score"]/text()'))
