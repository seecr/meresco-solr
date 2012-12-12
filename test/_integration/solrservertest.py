
from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest

class SolrServerTest(IntegrationTestCase): 
    def testAdminPingInterface(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/admin/ping', parse=True)
        self.assertEquals(['OK'], body.xpath('/response/str[@name="status"]/text()'))

    def testAdminInterface(self):
        header, body = getRequest(port=self.solrPort, path='/solr/#', parse=False)
        self.assertTrue('<title>Solr Admin</title>' in body, body)
