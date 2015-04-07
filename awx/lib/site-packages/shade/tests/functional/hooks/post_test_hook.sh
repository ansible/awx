# -*- coding: utf-8 -*-

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

export SHADE_DIR="$BASE/new/shade"

cd $BASE/new/devstack
source openrc admin admin
unset OS_CACERT

cd $SHADE_DIR
sudo chown -R jenkins:stack $SHADE_DIR
echo "Running shade functional test suite"
set +e
sudo -E -H -u jenkins tox -efunctional
EXIT_CODE=$?
set -e

exit $EXIT_CODE
