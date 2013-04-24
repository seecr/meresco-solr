## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase, CallTrace

from meresco.core import Observable, TransactionScope, Transaction
from meresco.solr.fields2solrdoc import Fields2SolrDoc
from meresco.solr import JOINHASH_PREFIX
from weightless.core import be, compose
from StringIO import StringIO
from lxml.etree import parse


class Fields2SolrDocTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        ctx = CallTrace('CTX')
        tx = Transaction('TX')
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
        self.assertEquals({'field_one': ['valueOne', 'anotherValueOne'], 'field_two': ['value<Two>']}, self.fxf.ctx.tx.objectScope(self.fxf))
        list(compose(self.fxf.commit(self.fxf.ctx.tx.getId())))
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals({'__id__':['iden&tifier'], 'field_one':['valueOne', 'anotherValueOne'], 'field_two': ['value<Two>'], JOINHASH_PREFIX + '__id__': [str(hash('iden&tifier'))]}, todict(kwargs['data']))

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
        self.assertEquals((), method.args)
        self.assertEquals('an:identifier', method.kwargs['identifier'])
        self.assertEquals('fields-partname', method.kwargs['partname'])
        self.assertEquals({'__id__': ['an:identifier'], 'field.name':['MyName', 'AnotherName'], 'field.title': ['MyDocument'], JOINHASH_PREFIX + '__id__': [str(hash('an:identifier'))]}, todict(method.kwargs['data']))

        expectedXml = """<doc xmlns=''><field name="__id__">an:identifier</field><field name="joinhash.__id__">%s</field><field name="field.title">MyDocument</field><field name="field.name">MyName</field><field name="field.name">AnotherName</field></doc>""" % hash('an:identifier')
        self.assertEquals(expectedXml, method.kwargs['data'])

    def testSingularValueFields(self):
        __callstack_var_tx__ = Transaction('name')
        __callstack_var_tx__.locals['id'] = 'identifier'
        observer = CallTrace('observer', emptyGeneratorMethods=['add'])
        fxf = Fields2SolrDoc('name', 'partname', singularValueFields=['once'])
        fxf.addObserver(observer)
        fxf.begin(name='name')
        fxf.addField('once', 'one')
        fxf.addField('once', 'two')
        fxf.addField('twice', 'one')
        fxf.addField('twice', 'two')
        list(compose(fxf.commit(__callstack_var_tx__.getId())))
        method = observer.calledMethods[0]
        self.assertEquals({'__id__': ['identifier'], 'once':['one'], 'twice': ['one', 'two'], JOINHASH_PREFIX + '__id__': [str(hash('identifier'))]}, todict(method.kwargs['data']))

    def testIsSingularValueField(self):
        __callstack_var_tx__ = Transaction('name')
        __callstack_var_tx__.locals['id'] = 'identifier'
        observer = CallTrace('observer', emptyGeneratorMethods=['add'])
        fxf = Fields2SolrDoc('name', 'partname', isSingularValueField=lambda name: name == 'once')
        fxf.addObserver(observer)
        fxf.begin(name='name')
        fxf.addField('once', 'one')
        fxf.addField('once', 'two')
        fxf.addField('twice', 'one')
        fxf.addField('twice', 'two')
        list(compose(fxf.commit(__callstack_var_tx__.getId())))
        method = observer.calledMethods[0]
        self.assertEquals({'__id__': ['identifier'], 'once':['one'], 'twice': ['one', 'two'], JOINHASH_PREFIX + '__id__': [str(hash('identifier'))]}, todict(method.kwargs['data']))

    def testChooseSingularValueFieldsOrIsSingularValueField(self):
        self.assertRaises(ValueError, lambda: Fields2SolrDoc('name', singularValueFields=['fields'], isSingularValueField=lambda name: False))


def add(identifier, partname, data):
    return
    yield

def todict(data):
    result = {}
    for field in parse(StringIO(data)).xpath('/doc/field'):
        result.setdefault(field.attrib['name'], []).append(field.text)
    return result
