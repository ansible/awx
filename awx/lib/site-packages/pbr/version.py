
#    Copyright 2012 OpenStack Foundation
#    Copyright 2012-2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utilities for consuming the version from pkg_resources.
"""

import pkg_resources


class VersionInfo(object):

    def __init__(self, package):
        """Object that understands versioning for a package
        :param package: name of the python package, such as glance, or
                        python-glanceclient
        """
        self.package = package
        self.release = None
        self.version = None
        self._cached_version = None

    def __str__(self):
        """Make the VersionInfo object behave like a string."""
        return self.version_string()

    def __repr__(self):
        """Include the name."""
        return "VersionInfo(%s:%s)" % (self.package, self.version_string())

    def _get_version_from_pkg_resources(self):
        """Get the version of the package from the pkg_resources record
        associated with the package.
        """
        try:
            requirement = pkg_resources.Requirement.parse(self.package)
            provider = pkg_resources.get_provider(requirement)
            return provider.version
        except pkg_resources.DistributionNotFound:
            # The most likely cause for this is running tests in a tree
            # produced from a tarball where the package itself has not been
            # installed into anything. Revert to setup-time logic.
            from pbr import packaging
            return packaging.get_version(self.package)

    def release_string(self):
        """Return the full version of the package including suffixes indicating
        VCS status.
        """
        if self.release is None:
            self.release = self._get_version_from_pkg_resources()

        return self.release

    def version_string(self):
        """Return the short version minus any alpha/beta tags."""
        if self.version is None:
            parts = []
            for part in self.release_string().split('.'):
                if part[0].isdigit():
                    parts.append(part)
                else:
                    break
            self.version = ".".join(parts)

        return self.version

    # Compatibility functions
    canonical_version_string = version_string
    version_string_with_vcs = release_string

    def cached_version_string(self, prefix=""):
        """Generate an object which will expand in a string context to
        the results of version_string(). We do this so that don't
        call into pkg_resources every time we start up a program when
        passing version information into the CONF constructor, but
        rather only do the calculation when and if a version is requested
        """
        if not self._cached_version:
            self._cached_version = "%s%s" % (prefix,
                                             self.version_string())
        return self._cached_version
