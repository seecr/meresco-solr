#!/bin/bash
## begin license ##
#
# "Meresco Solr" is a set of components and tools
#  to integrate Solr into "Meresco."
#
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
export LANG=en_US.UTF-8
export PYTHONPATH=.:"$PYTHONPATH"

tests="client server"
pyversions="python2.6"
if [ -e /usr/bin/python2.7 ]; then
    pyversions="python2.7"
fi
for option in $1 $2; do
    if [ "$option" == "--client" ]; then
        tests="client"
        shift
    elif [ "$option" == "--server" ]; then
        tests="server"
        shift
    fi
    if [ "${option:0:10}" == "--python2." ]; then
        shift
        pyversions="${option:2}"
    fi
done



for type in $tests; do
    if [ "$type" == "client" ]; then
        echo 'Meresco-Solr Client test'
        echo Found Python versions: $pyversions
        for pycmd in $pyversions; do
            echo "================ $pycmd _alltests.py $@ ================"
            $pycmd _alltests.py "$@"
        done
    fi
    if [ "$type" == "server" ]; then
        echo 'Meresco-Solr Server test'
        (
            echo 'No unit tests yet for server Java code'
#            cd ../src/test
#            ./alltests.sh "$@"
        )
    fi
done
