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
option=$1
if [ "$option" == "--client" ]; then
    tests="client"
    shift
elif [ "$option" == "--server" ]; then
    tests="server"
    shift
fi

for type in $tests; do
    if [ "$type" == "client" ]; then
        echo 'Meresco-Solr Client test'
        python2.6 _alltests.py "$@"
    fi
    if [ "$type" == "server" ]; then
        echo 'Meresco-Solr Server test'
        (
            cd ..
            ./build.sh
        )
        (
            cd ../src/test
            ./alltests.sh "$@"
        )
    fi
done
