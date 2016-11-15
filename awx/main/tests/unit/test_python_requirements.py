
import os
from pip.operations import freeze

from django.conf import settings

def test_env_matches_requirements_txt():

    def check_is_in(src, dests):
        if src not in dests:
            print("%s not in" % src)
            return False
        return True

    base_dir = settings.BASE_DIR
    requirements_path = os.path.join(base_dir, '../', 'requirements/requirements.txt')

    reqs_actual = []
    xs = freeze.freeze(local_only=True, requirement=requirements_path)
    for x in xs:
        if '## The following requirements were added by pip freeze' in x:
            break
        reqs_actual.append(x.split('=='))

    reqs_expected = []
    with open(requirements_path) as f:
        for line in f:
            line.rstrip()
            # TODO: process git requiremenst and use egg
            if line.strip().startswith('#') or line.strip().startswith('git'):
                continue
            if line.startswith('-e'):
                continue
            line.rstrip()
            reqs_expected.append(line.rstrip().split('=='))
    
    not_found = []
    for r in reqs_expected:
        res = check_is_in(r, reqs_actual)
        if res is False:
            not_found.append(r)

    if len(not_found) > 0:
        raise RuntimeError("%s not found in \n\n%s" % (not_found, reqs_actual))


