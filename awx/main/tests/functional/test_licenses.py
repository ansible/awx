
import glob
import json
import os

from django.conf import settings

try:
    from pip._internal.req import parse_requirements
except ImportError:
    from pip.req import parse_requirements


def test_python_and_js_licenses():

    def index_licenses(path):
        # Check for GPL (forbidden) and LGPL (need to ship source)
        # This is not meant to be an exhaustive check.
        def check_license(license_file):
            with open(license_file) as f:
                data = f.read()
                is_lgpl = 'GNU LESSER GENERAL PUBLIC LICENSE' in data.upper()
                # The LGPL refers to the GPL in-text
                # Case-sensitive for GPL to match license text and not PSF license reference
                is_gpl = 'GNU GENERAL PUBLIC LICENSE' in data and not is_lgpl
                return (is_gpl, is_lgpl)

        def find_embedded_source_version(path, name):
            for entry in os.listdir(path):
                # Check variations of '-' and '_' in filenames due to python
                for fname in [name, name.replace('-','_')]:
                    if entry.startswith(fname) and entry.endswith('.tar.gz'):
                        v = entry.split(name + '-')[1].split('.tar.gz')[0]
                        return v
            return None

        list = {}
        for txt_file in glob.glob('%s/*.txt' % path):
            filename = txt_file.split('/')[-1]
            name = filename[:-4].lower()
            (is_gpl, is_lgpl) = check_license(txt_file)
            list[name] = {
                'name': name,
                'filename': filename,
                'gpl': is_gpl,
                'source_required': (is_gpl or is_lgpl),
                'source_version': find_embedded_source_version(path, name)
            }
        return list

    def read_api_requirements(path):
        ret = {}
        for req_file in ['requirements.txt', 'requirements_ansible.txt', 'requirements_git.txt', 'requirements_ansible_git.txt']:
            fname = '%s/%s' % (path, req_file)

            for reqt in parse_requirements(fname, session=''):
                name = reqt.name
                version = str(reqt.specifier)
                if version.startswith('=='):
                    version=version[2:]
                if reqt.link:
                    (name, version) = reqt.link.filename.split('@',1)
                    if name.endswith('.git'):
                        name = name[:-4]
                ret[name] = { 'name': name, 'version': version}
        return ret


    def read_ui_requirements(path):
        def json_deps(jsondata):
            ret = {}
            deps = jsondata.get('dependencies',{})
            for key in deps.keys():
                key = key.lower()
                devonly = deps[key].get('dev',False)
                if not devonly:
                    if key not in ret.keys():
                        depname = key.replace('/','-')
                        ret[depname] = {
                            'name': depname,
                            'version': deps[key]['version']
                        }
                        ret.update(json_deps(deps[key]))
            return ret

        with open('%s/package-lock.json' % path) as f:
            jsondata = json.load(f)
            return json_deps(jsondata)

    def remediate_licenses_and_requirements(licenses, requirements):
        errors = []
        items = list(licenses.keys())
        items.sort()
        for item in items:
            if item not in [r.lower() for r in requirements.keys()] and item != 'awx':
                errors.append(" license file %s does not correspond to an existing requirement; it should be removed." % (licenses[item]['filename'],))
                continue
            # uWSGI has a linking exception
            if licenses[item]['gpl'] and item != 'uwsgi':
                errors.append(" license for %s is GPL. This software cannot be used." % (item,))
            if licenses[item]['source_required']:
                version = requirements[item]['version']
                if version != licenses[item]['source_version']:
                    errors.append(" embedded source for %s is %s instead of the required version %s" % (item, licenses[item]['source_version'], version))
            elif licenses[item]['source_version']:
                errors.append(" embedded source version %s for %s is included despite not being needed" % (licenses[item]['source_version'],item))
        items = list(requirements.keys())
        items.sort()
        for item in items:
            if item.lower() not in licenses.keys():
                errors.append(" license for requirement %s is missing" %(item,))
        return errors

    base_dir = settings.BASE_DIR
    api_licenses = index_licenses('%s/../docs/licenses' % base_dir)
    ui_licenses = index_licenses('%s/../docs/licenses/ui' % base_dir)
    api_requirements = read_api_requirements('%s/../requirements' % base_dir)
    ui_requirements = read_ui_requirements('%s/ui' % base_dir)

    errors = []
    errors += remediate_licenses_and_requirements(ui_licenses, ui_requirements)
    errors += remediate_licenses_and_requirements(api_licenses, api_requirements)
    if errors:
        raise Exception('Included licenses not consistent with requirements:\n%s' %
                        '\n'.join(errors))
