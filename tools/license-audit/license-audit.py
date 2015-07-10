#!/usr/bin/python
#
# Parse out as much licensing information as we can from our vendored directories to create a license report.
# You may need to edit this afterwords to replace any 'UNKNOWN' with actual data.

import csv
import fnmatch
import json
import os
import re
import sys

import yolk.pypi

def usage():
    print "license-audit.py <path to tower source> <infile> [<outfile>]"
    sys.exit(1)

def read_requirements(towerpath):
    filename = '%s/awx/lib/site-packages/README' % (towerpath,)
    ret = {}
    f = open(filename)
    if not f:
        print "failed to open %s" %(filename,)
        return None
    data = f.readlines()
    f.close()
    for line in data:
        if '==' in line:
            m = re.match(r"(\S+)==(\S+) \((\S+)",line)
            if m:
                name = m.group(1)
                version = m.group(2)
                pathname = m.group(3)
                if pathname.endswith(',') or pathname.endswith(')'):
                    pathname = pathname[:-1]
                if pathname.endswith('/*'):
                    pathname = pathname[:-2]
                item = {}
                item['name'] = name
                item['version'] = version
                item['path'] = pathname
                ret[name] = item
    return ret

def get_python(towerpath):
    excludes = [ 'README*', '*.dist-info', 'funtests', 'easy_install.py', 'oslo', 'pkg_resources', '_markerlib' ]
    directory = '%s/awx/lib/site-packages' % (towerpath,)
    dirlist = os.listdir(directory)
    ret = []
    for item in dirlist:
        use = True
        for exclude in excludes:
            if fnmatch.fnmatch(item, exclude):
                use = False
        if use:
            ret.append(item)
    return ret

def get_js(towerpath):
    excludes = [ ]
    directory = '%s/awx/ui/static/lib' % (towerpath,)
    dirlist = os.listdir(directory)
    ret = {}
    for item in dirlist:
        use = True
        for exclude in excludes:
            if fnmatch.fnmatch(item, exclude):
                use = False
        if use:
            try:
                bowerfile = open('%s/%s/bower.json' %(directory, item))
            except:
                # add dummy entry (should read package.json if it exists)
                pkg = {}
                pkg['name'] = item
                pkg['license'] = 'UNKNOWN'
                pkg['url'] = 'UNKNOWN'
                ret[item] = pkg
                continue
            pkginfo = json.load(bowerfile)
            bowerfile.close()
            pkg = {}
            pkg['name'] = item
            if pkginfo.has_key('license'):
                pkg['license'] = normalize_license(pkginfo['license'])
            else:
                pkg['license'] = 'UNKNOWN'
            if pkginfo.has_key('homepage'):
                pkg['url'] = pkginfo['homepage']
            elif pkginfo.has_key('url'):
                pkg['url'] = pkginfo['url']
            else:
                pkg['url'] = 'UNKNOWN'
            ret[item] = pkg
    return ret


def search_requirements(requirements_dict, path):
    for item in requirements_dict.values():
        if item['path'] == path:
            return True
    return False

def normalize_license(license):
    if not license:
        return 'UNKNOWN'
    license = license.replace('"','')
    if license == 'None':
        return 'UNKNOWN'
    if license in ['Apache License, Version 2.0', 'Apache License (2.0)', 'Apache License 2.0', 'Apache-2.0', 'Apache License, v2.0']:
        return 'Apache 2.0'
    if license == 'ISC license':
        return 'ISC'
    if license == 'MIT License' or license == 'MIT license':
        return 'MIT'
    if license == 'BSD License' or license == 'Simplified BSD':
        return 'BSD'
    if license == 'LGPL':
        return 'LGPL 2.1'
    # Don't embed YOUR ENTIRE LICENSE in your metadata!
    if license.find('Copyright 2011-2013 Jeffrey Gelens') != -1:
        return 'Apache 2.0'
    if license.find('https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/LICENSE') != -1:
        return 'MIT'
    if license == 'Python Software Foundation License':
        return 'PSF'
    return license

def read_csv(filename):
    ret = {}
    f = open(filename)
    if not f:
        print "failed to open %s" %(filename,)
        return None
    reader = csv.reader(f, delimiter=',')
    for line in reader:
        item = {}
        item['name'] = line[0]
        item['license'] = line[1]
        item['url'] = line[2]
        item['source'] = line[3]
        ret[line[0]] = item
    return ret
   
def write_csv(filename, data):
    keys = data.keys()
    keys.sort()
    csvfile = open(filename, 'wb') 
    writer = csv.writer(csvfile, delimiter = ',', lineterminator = '\n')
    for key in keys:
        item = data[key]
        l = (item['name'],item['license'],item['url'],item['source'])
        writer.writerow(l)
    csvfile.close()
        

if len(sys.argv) < 3:
    usage()

if len(sys.argv) < 4:
    outputfile = sys.stdout
else:
    outputfile = sys.argv[3]

tower_path = sys.argv[1]

# Read old license CSV
olddata = read_csv(sys.argv[2])

# Read python site-packages README requirements file
requirements = read_requirements(tower_path)

if not olddata or not requirements:
    print "No starting data"
    sys.exit(1)

# Get directory of vendored things from site-packages...
python_packages = get_python(tower_path)

# ... and ensure they're noted in the requirements file
ok = True
for package in python_packages:
    if not search_requirements(requirements, package):
        print "%s not in requirements!" % (package,)
        ok = False
if not ok:
    sys.exit(1)


# See if there's pip things in our current license list that we don't have now
reqs = requirements.keys()
for item in olddata.values():
    if item['source'] == 'pip' and item['name'] not in reqs:
        print "No longer vendoring %s" %(item['name'],)

# Get directory of vendored JS things from the js dir
js_packages = get_js(tower_path)

# See if there's JS things in our current license list that we don't have now
js = js_packages.keys()
for item in olddata.values():
    if item['source'] == 'js' and item['name'] not in js:
        print "No longer vendoring %s" %(item['name'],)

# Take the requirements file, and get license information where necessary
cs = yolk.pypi.CheeseShop()
for req in requirements.values():
    cs_info = cs.release_data(req['name'],req['version'])
    if not cs_info:
        print "Couldn't find '%s-%s'" %(req['name'],req['version'])
        if not olddata.has_key(req['name']):
            print "... and it's not in the current data. This needs fixed!"
            sys.exit(1)
        continue
    license = normalize_license(cs_info['license'])
    url = cs_info['home_page']
    try:
        data = olddata[req['name']]
    except:
        print "New item %s" %(req['name'])
        item = {}
        item['name'] = req['name']
        item['license'] = license
        item['url'] = url
        item['source'] = 'pip'
        olddata[req['name']] = item
        continue
    if license != 'UNKNOWN' and license != data['license']:
        data['license'] = license
    if url != 'UNKNOWN' and url != data['url']:
        data['url'] = url

# Update JS package info
for pkg in js:
    if olddata.has_key(pkg):
        data = olddata[pkg]
        new = js_packages[pkg]
        if new['license'] != 'UNKNOWN' and new['license'] != data['license']:
            data['license'] = new['license']
        if new['url'] != 'UNKNOWN' and new['url'] != data['url']:
            data['url'] = new['url']
    else:
        item = {}
        item['name'] = pkg
        item['license'] = js_packages[pkg]['license']
        item['url'] = js_packages[pkg]['url']
        item['source'] = 'js'
        olddata[pkg] = item
        continue

write_csv(outputfile, olddata)