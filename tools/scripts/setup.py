# This file only exists for the purposes of generating the development environment's awx.egg-info file
# because pip install -e is painfully slow. If anyone finds a better way to do this, I'll buy you a drink.

import setuptools
from setuptools.command.egg_info import egg_info as _egg_info


class egg_info_dev(_egg_info):
    def find_sources(self):
        # when we generate a .egg-info for the development
        # environment, it's not really critical that we
        # parse the MANIFEST.in (which is actually quite expensive
        # in Docker for Mac)
        pass


if __name__ == "__main__":
    setuptools.setup(
        cmdclass={'egg_info_dev': egg_info_dev},
    )
