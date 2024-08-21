import glob
import os

from django.conf import settings

try:
    from pip._internal.req import parse_requirements
except ImportError:
    from pip.req import parse_requirements

from pip._internal.req.constructors import parse_req_from_line


def check_license(license_file):
    with open(license_file) as f:
        data = f.read()
        is_lgpl = 'GNU LESSER GENERAL PUBLIC LICENSE' in data.upper()
        is_gpl = 'GNU GENERAL PUBLIC LICENSE' in data and not is_lgpl
        return is_gpl, is_lgpl


def find_embedded_source_version(path, name):
    files = os.listdir(path)
    tgz_files = [f for f in files if f.endswith('.tar.gz')]
    for tgz in tgz_files:
        pkg_name = tgz.split('-')[0].split('_')[0]
        if pkg_name == name:
            return tgz.split('-')[1].split('.tar.gz')[0]
    return None


def index_licenses(path):
    licenses = {}
    for txt_file in glob.glob(f'{path}/*.txt'):
        filename = os.path.basename(txt_file)
        name = filename[:-4].lower()
        is_gpl, is_lgpl = check_license(txt_file)
        licenses[name] = {
            'name': name,
            'filename': filename,
            'gpl': is_gpl,
            'source_required': is_gpl or is_lgpl,
            'source_version': find_embedded_source_version(path, name),
        }
    return licenses


def parse_requirement(reqt):
    parsed_requirement = parse_req_from_line(reqt.requirement, None)
    name = parsed_requirement.requirement.name
    version = str(parsed_requirement.requirement.specifier)
    if version.startswith('=='):
        version = version[2:]
    if parsed_requirement.link:
        if str(parsed_requirement.link).startswith(('http://', 'https://')):
            name, version = str(parsed_requirement.requirement).split('==', 1)
        else:
            name, version = parsed_requirement.link.filename.split('@', 1)
        if name.endswith('.git'):
            name = name[:-4]
        if name == 'receptor':
            name = 'receptorctl'
    return name, version


def read_api_requirements(path):
    requirements = {}
    skip_pbr_license_check = False
    for req_file in ['requirements.txt', 'requirements_git.txt']:
        fname = f'{path}/{req_file}'
        for reqt in parse_requirements(fname, session=''):
            name, version = parse_requirement(reqt)
            if name == 'ansible-runner':
                skip_pbr_license_check = True
            requirements[name] = {'name': name, 'version': version}
    if 'pbr' in requirements and skip_pbr_license_check:
        del requirements['pbr']
    return requirements


def remediate_licenses_and_requirements(licenses, requirements):
    errors = []
    for item in sorted(licenses.keys()):
        if item not in [r.lower() for r in requirements.keys()] and item != 'awx':
            errors.append(f" license file {licenses[item]['filename']} does not correspond to an existing requirement; it should be removed.")
            continue
        if licenses[item]['gpl'] and item != 'uwsgi':
            errors.append(f" license for {item} is GPL. This software cannot be used.")
        if licenses[item]['source_required']:
            version = requirements[item]['version']
            if version != licenses[item]['source_version']:
                errors.append(f" embedded source for {item} is {licenses[item]['source_version']} instead of the required version {version}")
        elif licenses[item]['source_version']:
            errors.append(f" embedded source version {licenses[item]['source_version']} for {item} is included despite not being needed")
    for item in sorted(requirements.keys()):
        if item.lower() not in licenses.keys():
            errors.append(f" license for requirement {item} is missing")
    return errors


def test_python_licenses():
    base_dir = settings.BASE_DIR
    api_licenses = index_licenses(f'{base_dir}/../licenses')
    api_requirements = read_api_requirements(f'{base_dir}/../requirements')

    errors = remediate_licenses_and_requirements(api_licenses, api_requirements)
    if errors:
        raise Exception('Included licenses not consistent with requirements:\n%s' % '\n'.join(errors))
