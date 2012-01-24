## begin license ##
# 
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco." 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

from cq2utils import CQ2TestCase, CallTrace

from meresco.core import Observable, TransactionScope
from meresco.solr.fields2solrdoc import Fields2SolrDoc
from weightless.core import be, compose

def add(identifier, partname, data):
    return
    yield

class Fields2SolrDocTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)

        ctx = CallTrace('CTX')
        tx = CallTrace('TX')
        tx.locals = {'id': 'iden&tifier'}
        tx.name = "tsName"
        self.fxf = Fields2SolrDoc("tsName", "fields-partname")
        self.fxf.ctx = ctx 
        self.fxf.ctx.tx = tx
        self.observer = CallTrace(methods={'add': add})
        self.fxf.addObserver(self.observer)

    def testCreateXml(self):
        self.fxf.begin(name="tsName")
        self.fxf.addField("field_one", "valueOne")
        self.fxf.addField("field_one", "anotherValueOne")
        self.fxf.addField("field_two", "value<Two>")
        list(compose(self.fxf.commit(self.fxf.ctx.tx.getId())))
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEqualsWS('<doc><field name="__id__">iden&amp;tifier</field><field name="field_one">valueOne</field><field name="field_one">anotherValueOne</field><field name="field_two">value&lt;Two&gt;</field></doc>', kwargs['data'])

    def testCollectAllTerms(self):
        fields = [("key_1", "value_1"), ("key_1", "value_2"), ("key_2", "value_3"), ("key_3", "value_1"), ("key_3", "value_2"), ("key_3", "value_4")]

        self.assertEquals(set([]), self.fxf._terms([]))
        self.assertEquals(set(['value_1', 'value_2', 'value_3', 'value_4']), self.fxf._terms(fields))

    def testWorksWithRealTransactionScope(self):
        intercept = CallTrace('Intercept', ignoredAttributes=['begin', 'commit', 'rollback'], methods={'add': add})
        class MockVenturi(Observable):
            def all_unknown(self, message, *args, **kwargs):
                self.ctx.tx.locals['id'] = 'an:identifier'
                yield self.all.unknown(message, *args, **kwargs)
        class MockMultiFielder(Observable):
            def add(self, *args, **kwargs):
                self.do.addField('field.name', 'MyName')
                self.do.addField('field.name', 'AnotherName')
                self.do.addField('field.title', 'MyDocument')
                yield 'ok'
        root = be( 
            (Observable(),
                (TransactionScope(transactionName="solrDoc"),
                    (MockVenturi(),
                        (MockMultiFielder(),
                            (Fields2SolrDoc("solrDoc", "fields-partname"),
                                (intercept,),
                            )   
                        )   
                    )   
                )   
            )   
        )   
        list(compose(root.all.add('some', 'arguments')))
        self.assertEquals(['add'], [m.name for m in intercept.calledMethods])
        method = intercept.calledMethods[0]
        expectedXml = """<doc><field name="__id__">an:identifier</field><field name="field.name">MyName</field><field name="field.name">AnotherName</field><field name="field.title">MyDocument</field></doc>"""
        self.assertEquals(((), {'identifier': 'an:identifier', 'partname': 'fields-partname', 'data': expectedXml}), (method.args, method.kwargs))
 
