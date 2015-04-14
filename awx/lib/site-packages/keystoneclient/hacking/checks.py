# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""python-keystoneclient's pep8 extensions.

In order to make the review process faster and easier for core devs we are
adding some python-keystoneclient specific pep8 checks. This will catch common
errors so that core devs don't have to.

"""


import re


def check_oslo_namespace_imports(logical_line, blank_before, filename):
    oslo_namespace_imports = re.compile(
        r"(((from)|(import))\s+oslo\.)|(from\s+oslo\s+import\s+)")

    if re.match(oslo_namespace_imports, logical_line):
        msg = ("K333: '%s' must be used instead of '%s'.") % (
            logical_line.replace('oslo.', 'oslo_'),
            logical_line)
        yield(0, msg)


def factory(register):
    register(check_oslo_namespace_imports)
