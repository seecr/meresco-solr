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

from os import system
from sys import path, argv
from unittest import main

system('find .. -name "*.pyc" | xargs rm -f')
from glob import glob
for dir in glob('../deps.d/*'):
    path.insert(0, dir)
path.insert(0, "..")

from fields2solrdoctest import Fields2SolrDocTest
from solrinterfacetest import SolrInterfaceTest
from solrlucenequerycomposertest import SolrLuceneQueryComposerTest
from cql2solrlucenequerytest import CQL2SolrLuceneQueryTest

if __name__ == '__main__':
    main()

