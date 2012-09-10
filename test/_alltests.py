## begin license ##
# 
# All rights reserved.
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
## end license ##

import os, sys
os.system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

sys.path.insert(0, '../bin')

from unittest import main

from solrruntest import SolrRunTest

if __name__ == '__main__':
    main()

