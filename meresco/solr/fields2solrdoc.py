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

from meresco.core import Observable
from xml.sax.saxutils import escape as escapeXml
from itertools import chain
from solrinterface import JOINHASH_PREFIX

class Fields2SolrDoc(Observable):
    def __init__(self, transactionName, partname="solr", singularValueFields=None, isSingularValueField=None):
        Observable.__init__(self)
        self._transactionName = transactionName
        self._partname = partname
        if singularValueFields and isSingularValueField:
            raise ValueError("Use either 'singularValueFields' or 'isSingularValueField'")
        self._isSingularValueField = isSingularValueField
        if singularValueFields:
            singularValueFields = set(singularValueFields)
            self._isSingularValueField = lambda name: name in singularValueFields

    def begin(self, name):
        if name != self._transactionName:
            return
        tx = self.ctx.tx
        tx.join(self)

    def addField(self, name, value):
        tx = self.ctx.tx
        valueList = tx.objectScope(self).setdefault(name, [])
        if not self._isSingularValueField is None:
            if len(valueList) == 1 and self._isSingularValueField(name):
                return
        valueList.append(value)

    def commit(self, id):
        tx = self.ctx.tx
        fields = tx.objectScope(self)
        if not fields:
            return
        recordIdentifier = tx.locals["id"]
        specialFields = [
            ('__id__', recordIdentifier), 
            (JOINHASH_PREFIX + '__id__', str(hash(recordIdentifier))), 
        ] 
        def fieldStatement(key, value):
            return '<field name="%s">%s</field>' % (escapeXml(key), escapeXml(value))
        allFields = ((k, v) for k, vs in fields.items() for v in vs)
        xml = "<doc xmlns=''>%s</doc>" % ''.join(fieldStatement(*args) for args in chain(iter(specialFields), allFields))
        yield self.all.add(identifier=recordIdentifier, partname=self._partname, data=xml)
