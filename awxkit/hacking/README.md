'Hacking' directory tools
=========================

env-setup
---------

The 'env-setup' script modifies your environment to allow you to run
awxkit from a git checkout using python3.

First, Set up your environment to run from the checkout:

    $ source ./hacking/env-setup

Then, you can confirm `awx` and `akit` command as follows:

    $ awx --help
    $ akit --help
