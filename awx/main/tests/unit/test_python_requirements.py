from pip.operations import freeze
from django.conf import settings

def test_req():
    def check_is_in(src, dests):
        if src not in dests:
            src2 = [src[0].replace('_', '-'), src[1]]
            if src2 not in dests:
                print("%s not in" % src2) 
                return False
            else:
                print("%s not in" % src)
                return False
        return True

    base_dir = settings.BASE_DIR

    reqs_actual = []
    xs = freeze.freeze(local_only=True, requirement=base_dir + "/../requirements/requirements.txt")
    for x in xs:
        if '## The following requirements were added by pip freeze' in x:
            break
        reqs_actual.append(x.split('=='))

    reqs_expected = []
    with open(base_dir + "/../requirements/requirements.txt") as f:
        for line in f:
            line.rstrip()
            # TODO: process git requiremenst and use egg
            if line.strip().startswith('#') or line.strip().startswith('git'):
                continue
            if line.startswith('-e'):
                continue
            line.rstrip()
            reqs_expected.append(line.rstrip().split('=='))
    
    for r in reqs_actual:
        print(r)

    not_found = []
    for r in reqs_expected:
        res = check_is_in(r, reqs_actual)
        if res is False:
            not_found.append(r)

    raise RuntimeError("%s not found in \n\n%s" % (not_found, reqs_expected))


