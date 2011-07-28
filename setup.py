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

from distutils.core import setup

setup(
    name='meresco-solr',
    packages=[
        'meresco.solr',
    ],
    version='%VERSION%',
    url='http://www.meresco.org',
    author='Seecr (Seek You Too B.V.)',
    author_email='info@seecr.nl',
    description='Meresco Solr is a set of components and tools to integrate Solr into Meresco.',
    long_description='Meresco Solr is a set of components and tools to integrate Solr into Meresco.',
    license='GNU Public License',
    platforms='all',
)
