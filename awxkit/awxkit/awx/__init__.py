from packaging.version import Version


def version_cmp(x, y):
    """Compare two version strings.
    Returns -1 if x < y, 0 if x == y, 1 if x > y
    """
    vx = Version(x)
    vy = Version(y)
    if vx < vy:
        return -1
    elif vx > vy:
        return 1
    else:
        return 0
