

from seecr.test import IntegrationTestCase

class SolrServerTest(IntegrationTestCase): 
    def testAdminInterface(self):
        header, body = getRequest(port=self.solrPort, path='/solr/records/amdin', parse=False)
        self.assertEquals('Hallo wie is daar?' in body, body)
