# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Taken From Twisted Python which licensed under MIT license
# https://github.com/powdahound/twisted/blob/master/twisted/python/dist.py
# https://github.com/powdahound/twisted/blob/master/LICENSE

import os
import fnmatch

# Names that are excluded from globbing results:
EXCLUDE_NAMES = ['{arch}', 'CVS', '.cvsignore', '_darcs',
                 'RCS', 'SCCS', '.svn']
EXCLUDE_PATTERNS = ['*.py[cdo]', '*.s[ol]', '.#*', '*~', '*.py']


def _filter_names(names):
    """
    Given a list of file names, return those names that should be copied.
    """
    names = [n for n in names
             if n not in EXCLUDE_NAMES]
    # This is needed when building a distro from a working
    # copy (likely a checkout) rather than a pristine export:
    for pattern in EXCLUDE_PATTERNS:
        names = [n for n in names
                 if (not fnmatch.fnmatch(n, pattern))
                 and (not n.endswith('.py'))]
    return names


def relative_to(base, relativee):
    """
    Gets 'relativee' relative to 'basepath'.

    i.e.,

    >>> relative_to('/home/', '/home/radix/')
    'radix'
    >>> relative_to('.', '/home/radix/Projects/Twisted')
    'Projects/Twisted'

    The 'relativee' must be a child of 'basepath'.
    """
    basepath = os.path.abspath(base)
    relativee = os.path.abspath(relativee)
    if relativee.startswith(basepath):
        relative = relativee[len(basepath):]
        if relative.startswith(os.sep):
            relative = relative[1:]
        return os.path.join(base, relative)
    raise ValueError("%s is not a subpath of %s" % (relativee, basepath))


def get_packages(dname, pkgname=None, results=None, ignore=None, parent=None):
    """
    Get all packages which are under dname. This is necessary for
    Python 2.2's distutils. Pretty similar arguments to getDataFiles,
    including 'parent'.
    """
    parent = parent or ""
    prefix = []
    if parent:
        prefix = [parent]
    bname = os.path.basename(dname)
    ignore = ignore or []
    if bname in ignore:
        return []
    if results is None:
        results = []
    if pkgname is None:
        pkgname = []
    subfiles = os.listdir(dname)
    abssubfiles = [os.path.join(dname, x) for x in subfiles]

    if '__init__.py' in subfiles:
        results.append(prefix + pkgname + [bname])
        for subdir in filter(os.path.isdir, abssubfiles):
            get_packages(subdir, pkgname=pkgname + [bname],
                         results=results, ignore=ignore,
                         parent=parent)
    res = ['.'.join(result) for result in results]
    return res


def get_data_files(dname, ignore=None, parent=None):
    """
    Get all the data files that should be included in this distutils Project.

    'dname' should be the path to the package that you're distributing.

    'ignore' is a list of sub-packages to ignore.  This facilitates
    disparate package hierarchies.  That's a fancy way of saying that
    the 'twisted' package doesn't want to include the 'twisted.conch'
    package, so it will pass ['conch'] as the value.

    'parent' is necessary if you're distributing a subpackage like
    twisted.conch.  'dname' should point to 'twisted/conch' and 'parent'
    should point to 'twisted'.  This ensures that your data_files are
    generated correctly, only using relative paths for the first element
    of the tuple ('twisted/conch/*').
    The default 'parent' is the current working directory.
    """
    parent = parent or "."
    ignore = ignore or []
    result = []
    for directory, subdirectories, filenames in os.walk(dname):
        resultfiles = []
        for exname in EXCLUDE_NAMES:
            if exname in subdirectories:
                subdirectories.remove(exname)
        for ig in ignore:
            if ig in subdirectories:
                subdirectories.remove(ig)
        for filename in _filter_names(filenames):
            resultfiles.append(filename)
        if resultfiles:
            for filename in resultfiles:
                file_path = os.path.join(directory, filename)
                if parent:
                    file_path = file_path.replace(parent + os.sep, '')
                result.append(file_path)

    return result
