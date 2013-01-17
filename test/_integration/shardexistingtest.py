from StringIO import StringIO
from lxml.etree import parse

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest


class ShardExistingTest(IntegrationTestCase):
    def testShardExisting(self):
        shards = ','.join(
            "localhost:%s/solr/%s" % (solrState.solrPort, solrState.solrCore)
            for solrState in (
                self.solrStates[name] for name in ['edurep', 'zp']
            )
        )
        print 'shards:', shards
        header, body = getRequest(
            port=self.solrStates['zp'].solrPort,
            path="/solr/records/select",
            arguments={
                "q": 'wiskunde OR priemgetallen',
                'fl': '__id__,score',
                "debugQuery": "on",
                "shards": shards
            },
            parse=False)
        print header, body
        lxmlNode = parse(StringIO(body))
        self.assertEquals(set(['?']), set(lxmlNode.xpath('//doc/str[@name="__id__"]/text()')))
