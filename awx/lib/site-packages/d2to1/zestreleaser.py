"""zest.releaser entry points to support projects using distutils2-like
setup.cfg files.  The only actual functionality this adds is to update the
version option in a setup.cfg file, if it exists.  If setup.cfg does not exist,
or does not contain a version option, then this does nothing.

TODO: d2to1 theoretically supports using a different filename for setup.cfg;
this does not support that.  We could hack in support, though I'm not sure how
useful the original functionality is to begin with (and it might be removed) so
we ignore that for now.

TODO: There exists a proposal
(http://mail.python.org/pipermail/distutils-sig/2011-March/017628.html) to add
a 'version-from-file' option (or something of the like) to distutils2; if this
is added then support for it should be included here as well.
"""


import logging
import os

from .extern.six import print_
from .extern.six import moves as m
ConfigParser = m.configparser.ConfigParser


logger = logging.getLogger(__name__)



def update_setupcfg_version(filename, version):
    """Opens the given setup.cfg file, locates the version option in the
    [metadata] section, updates it to the new version.
    """

    setup_cfg = open(filename).readlines()
    current_section = None
    updated = False

    for idx, line in enumerate(setup_cfg):
        m = ConfigParser.SECTCRE.match(line)
        if m:
            if current_section == 'metadata':
                # We already parsed the entire metadata section without finding
                # a version line, and are now moving into a new section
                break
            current_section = m.group('header')
            continue

        if '=' not in line:
            continue

        opt, val = line.split('=', 1)
        opt, val = opt.strip(), val.strip()
        if current_section == 'metadata' and opt == 'version':
            setup_cfg[idx] = 'version = %s\n' % version
            updated = True
            break

    if updated:
        open(filename, 'w').writelines(setup_cfg)
        logger.info("Set %s's version to %r" % (os.path.basename(filename),
                                                version))


def prereleaser_middle(data):
    filename = os.path.join(data['workingdir'], 'setup.cfg')
    if os.path.exists(filename):
        update_setupcfg_version(filename, data['new_version'])


def releaser_middle(data):
    """
    releaser.middle hook to monkey-patch zest.releaser to support signed
    tagging--currently this is the only way to do this.  Also monkey-patches to
    disable an annoyance where zest.releaser only creates .zip source
    distributions.  This is supposedly a workaround for a bug in Python 2.4,
    but we don't care about Python 2.4.
    """

    import os
    import sys

    from zest.releaser.git import Git
    from zest.releaser.release import Releaser

    # Copied verbatim from zest.releaser, but with the cmd string modified to
    # use the -s option to create a signed tag
    def _my_create_tag(self, version):
        msg = "Tagging %s" % (version,)
        cmd = 'git tag -s %s -m "%s"' % (version, msg)
        if os.path.isdir('.git/svn'):
            print_("\nEXPERIMENTAL support for git-svn tagging!\n")
            cur_branch = open('.git/HEAD').read().strip().split('/')[-1]
            print_("You are on branch %s." % (cur_branch,))
            if cur_branch != 'master':
                print_("Only the master branch is supported for git-svn "
                       "tagging.")
                print_("Please tag yourself.")
                print_("'git tag' needs to list tag named %s." % (version,))
                sys.exit()
            cmd = [cmd]
            local_head = open('.git/refs/heads/master').read()
            trunk = open('.git/refs/remotes/trunk').read()
            if local_head != trunk:
                print_("Your local master diverges from trunk.\n")
                # dcommit before local tagging
                cmd.insert(0, 'git svn dcommit')
            # create tag in svn
            cmd.append('git svn tag -m "%s" %s' % (msg, version))
        return cmd

    # Similarly copied from zer.releaser to support use of 'v' in front
    # of the version number
    def _my_make_tag(self):
        from zest.releaser import utils
        from os import system

        if self.data['tag_already_exists']:
            return
        cmds = self.vcs.cmd_create_tag(self.data['version'])
        if not isinstance(cmds, list):
            cmds = [cmds]
        if len(cmds) == 1:
            print_("Tag needed to proceed, you can use the following command:")
        for cmd in cmds:
            print_(cmd)
            if utils.ask("Run this command"):
                print_(system(cmd))
            else:
                # all commands are needed in order to proceed normally
                print_("Please create a tag for %s yourself and rerun." % \
                        (self.data['version'],))
                sys.exit()
        if not self.vcs.tag_exists('v' + self.data['version']):
            print_("\nFailed to create tag %s!" % (self.data['version'],))
            sys.exit()

    # Normally all this does is to return '--formats=zip', which is currently
    # hard-coded as an option to always add to the sdist command; they ought to
    # make this actually optional
    def _my_sdist_options(self):
        return ''

    Git.cmd_create_tag = _my_create_tag
    Releaser._make_tag = _my_make_tag
    Releaser._sdist_options = _my_sdist_options


def postreleaser_before(data):
    """
    Fix the irritating .dev0 default appended to new development versions by
    zest.releaser to just append ".dev" without the "0".
    """

    data['dev_version_template'] = '%(new_version)s.dev'


def postreleaser_middle(data):
    filename = os.path.join(data['workingdir'], 'setup.cfg')
    if os.path.exists(filename):
        update_setupcfg_version(filename, data['dev_version'])
