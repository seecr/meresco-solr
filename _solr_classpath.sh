BUILDDIR=$1

SOLRWAR=/usr/share/java/webapps/apache-solr-4.0.0.war
SOLRWAR_DIR=$BUILDDIR/$(basename $SOLRWAR)
unzip -q -d $SOLRWAR_DIR $SOLRWAR
SOLRJARS=$(find $SOLRWAR_DIR/WEB-INF/lib -type f -name "*.jar")

CP="$(echo $SOLRJARS | tr ' ' ':')"
echo ${CP}
