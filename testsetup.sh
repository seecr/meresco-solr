#!/bin/bash
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

set -o errexit

rm -rf tmp build

fullPythonVersion=python2.6
${fullPythonVersion} setup.py install --root tmp


VERSION="x.y.z"

find tmp -name '*.py' -exec sed -r -e \
    "/DO_NOT_DISTRIBUTE/ d;
    s/\\\$Version:[^\\\$]*\\\$/\\\$Version: ${VERSION}\\\$/" -i '{}' \;

if [ -f /etc/debian_version ]; then
    SITE_PACKAGE_DIR=`pwd`/tmp/usr/local/lib/${fullPythonVersion}/dist-packages
else
    SITE_PACKAGE_DIR=`pwd`/tmp/usr/lib/${fullPythonVersion}/site-packages
fi

cp meresco/__init__.py ${SITE_PACKAGE_DIR}/meresco
export PYTHONPATH=${SITE_PACKAGE_DIR}:${PYTHONPATH}
cp -r test tmp/test

set +o errexit
(
cd tmp/test
./alltests.sh
)
set -o errexit

rm -rf tmp build

