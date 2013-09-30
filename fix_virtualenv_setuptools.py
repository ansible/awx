#!/usr/bin/env python
'''
Fix setuptools (in virtualenv) after upgrading to distribute >= 0.7.
'''

from distutils.sysconfig import get_python_lib
import glob
import os
import shutil

for f in glob.glob(os.path.join(get_python_lib(), 'setuptools-0.6*.egg*')):
    print 'removing', f
    if os.path.isdir(f):
        shutil.rmtree(f)
    else:
        os.remove(f)
