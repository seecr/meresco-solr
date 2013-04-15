#!/bin/bash
## begin license ##
#
# The Meresco Owlim package consists out of a HTTP server written in Java that
# provides access to an Owlim Triple store, as well as python bindings to
# communicate as a client with the server.
#
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# This file is part of "Meresco Owlim"
#
# "Meresco Owlim" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Owlim" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Owlim"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

VERSION=$1


SOLRWAR=/usr/share/java/webapps/apache-solr-4.0.0.war
BUILDDIR=./build
LIBDIR=usr-share/solr-data/lib
TARGET=meresco-solr.jar
if [ "${VERSION}" != "" ]; then
    TARGET=meresco-solr-${VERSION}.jar
fi

test -d $BUILDDIR && rm -r $BUILDDIR
mkdir $BUILDDIR

SOLRWAR_DIR=$BUILDDIR/$(basename $SOLRWAR)
unzip -q -d $SOLRWAR_DIR $SOLRWAR
SOLRJARS=$(find $SOLRWAR_DIR/WEB-INF/lib -type f -name "*.jar")

CP="$(echo $SOLRJARS | tr ' ' ':')"
javaFiles=$(find src/java -name "*.java")
echo "compiling" $javaFiles
javac -d $BUILDDIR -cp $CP $javaFiles
if [ "$?" != "0" ]; then
    echo "Build failed"
    exit 1
fi

jar -cf $LIBDIR/$TARGET -C $BUILDDIR org

rm -rf $BUILDDIR
