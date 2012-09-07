#!/bin/bash
mydir=$(cd $(dirname $0); pwd)
export PYTHONPATH=$(dirname $mydir)/bin:$PYTHONPATH
if [ "$(python -V 2>&1 | awk '{print $2}' | cut -c -3)" == "2.4" ]; then
    python2.5 ${mydir}/_solr-tests.py
else
    python ${mydir}/_solr-tests.py
fi
