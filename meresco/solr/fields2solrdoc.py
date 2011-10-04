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

from meresco.core import Observable
from xml.sax.saxutils import escape as escapeXml

class Fields2SolrDoc(Observable):
    def __init__(self, transactionName, partname):
        Observable.__init__(self)
        self._transactionName = transactionName
        self._partname = partname
        self.txs = {}

    def begin(self):
        tx = self.ctx.tx
        if tx.name != self._transactionName:
            return
        tx.join(self)
        self.txs[tx.getId()] = []

    def addField(self, name, value):
        tx = self.ctx.tx
        self.txs[tx.getId()].append((name, value))

    def commit(self):
        tx = self.ctx.tx
        fields = self.txs.pop(tx.getId())
        if not fields:
            return

        recordIdentifier = tx.locals["id"]
        specialFields = [
            ('__id__', recordIdentifier), 
        ] 
        def fieldStatement(key, value):
            return '<field name="%s">%s</field>' % (escapeXml(key), escapeXml(value))

        xml = "<doc>%s</doc>" % ''.join(fieldStatement(*args) for args in specialFields+fields)
        return self.asyncdo.add(identifier=recordIdentifier, partname=self._partname, data=xml)

    def _terms(self, fields):
        return set([value for (name, value) in fields])

