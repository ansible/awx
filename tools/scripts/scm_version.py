import datetime
import os
import sys
import subprocess
import traceback

AWX_SETUPTOOLS_SCM = True

try:
    from setuptools_scm import get_version
except ModuleNotFoundError:
    sys.stderr.write("Unable to import setuptools-scm, attempting to install now...\n")
    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    try:
        subprocess.check_output([sys.executable, '-m', 'ensurepip'], stderr=subprocess.STDOUT)
        subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'setuptools-scm'])
        import setuptools_scm

        get_version = setuptools_scm.get_version
    except subprocess.CalledProcessError as e:
        print('[debug]: {0}'.format(str(e)), file=sys.stderr)
        print('[debug]: output from exception: %s', e.output, file=sys.stderr)
        AWX_SETUPTOOLS_SCM = False
finally:
    if not AWX_SETUPTOOLS_SCM:
        print('Not using setuptools_scm', file=sys.stderr)
    else:
        print('Using setuptools_scm', file=sys.stderr)

if not AWX_SETUPTOOLS_SCM:
    # Conditionally define these to monkey patch only when no setuptools_scm
    def get_git_version():
        '''Get the version using git
        Returns:
        The same version string that setuptools-scm would return
        e.g., if git describe says 22.1.0-35-sha, return 22.1.1.dev35
        '''
        gitproc = None
        p = None
        try:
            p = subprocess.check_output(['which', 'git'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as cpe:
            print('[debug] CPE in get_git_version: {0}'.format(cpe), file=sys.stderr)
            print('[debug] returncode: {0}'.format(cpe.returncode), file=sys.stderr)
            print('[debug] output: {0}'.format(cpe.output), file=sys.stderr)
            print('[debug] proc: {0}'.format(p), file=sys.stderr)
        try:
            gitproc = subprocess.run(['git', 'describe', '--tags', '--dirty'], check=True, capture_output=True, text=True)
            ver = gitproc.stdout.strip()
            return ver
        except subprocess.CalledProcessError as cpe:
            print('[debug] CPE in get_git_version: {0}'.format(cpe), file=sys.stderr)
            print('[debug] returncode: {0}'.format(cpe.returncode), file=sys.stderr)
            print('[debug] output: {0}'.format(cpe.output), file=sys.stderr)
            print('[debug] gitproc: {0}'.format(gitproc), file=sys.stderr)
        except Exception as e:
            print('[debug] E in get_git_version: {0}'.format(e), file=sys.stderr)
            print('[debug] returncode: {0}'.format(e), file=sys.stderr)
            print('[debug] output: {0}'.format(e), file=sys.stderr)

    # TODO(jjwatt): rename to native_get_version or something and monkey patch if
    # setuptools-scm not available
    def get_version(*args, **kwargs):
        '''Get the version without using setuptools-scm
        Args:
        args: Any positional for compatibility (ignored).
        kwargs: Any keyword arg for compatibility (ignored).
        Returns:
        The same version string that setuptools-scm would return
        e.g., if git describe says 22.1.0-35-sha, return 22.1.1.dev35
        '''
        # This is the version that CI has been reporting, so we default to that as
        # a last resort. We will also return this if not in a `.git` dir.
        default_version = git_describe_version = '0.1.dev1'
        try:
            git_describe_version = get_git_version()
            print('[debug] gitdescribe ver: {0}'.format(git_describe_version), file=sys.stderr)
            bare_version, _, rest_version = git_describe_version.partition('-')
            distance, _, sha = rest_version.partition('-')
            version_parts = [int(i) for i in bare_version.split('.')]
            new_version_parts = version_parts[:2] + [version_parts[-1] + 1]
            new_base_version = '.'.join([str(i) for i in new_version_parts])
            setuptools_scm_version = f'{new_base_version}.dev{distance}+{sha}'
            print('[debug] setuptools_scm_version: {0}'.format(setuptools_scm_version), file=sys.stderr)
            # Now we're at, e.g., '22.1.1' and we need to add the distance
            # and other parts back in the setuptools-scm style.
            # if it's not dirty then it's this
            if 'dirty' not in sha:
                print('[debug]: in no dirty conditional', file=sys.stderr)
                return setuptools_scm_version
            else:
                # When it's dirty, setuptools-scm returns stuff like this:
                #   Example: '22.1.1.dev35-g765487390f.d20230425'
                # So, get the date in the right format and tack it on like
                # expected.
                print('[debug] in dirty conditional')
                setuptools_scm_version = setuptools_scm_version.removesuffix('-dirty')
                return '{v}.d{d}'.format(v=setuptools_scm_version, d=datetime.datetime.now().strftime('%Y%m%d'))
        except Exception as e:
            print('[debug] hit exception in munging: {0}'.format(str(e)), file=sys.stderr)
            print('[debug] trace: {0}'.format(e.__traceback__))
            return default_version


version = get_version(root='../..', relative_to=__file__)
print(version)
