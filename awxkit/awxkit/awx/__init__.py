from distutils.version import LooseVersion


def version_cmp(x, y):
    return LooseVersion(x)._cmp(y)
