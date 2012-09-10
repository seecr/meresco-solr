#!/bin/bash
## begin license ##
# 
# All rights reserved.
# 
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
## end license ##

export LANG=en_US.UTF-8
export PYTHONPATH=.:$PYTHONPATH
python _alltests.py "$@"
