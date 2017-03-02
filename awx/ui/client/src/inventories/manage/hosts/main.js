/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import HostsAddController from './hosts-add.controller';
import HostsEditController from './hosts-edit.controller';
import SetStatus from './factories/set-status.factory';
import SetEnabledMsg from './factories/set-enabled-msg.factory';

export default
angular.module('manageHosts', [])
    .factory('SetStatus', SetStatus)
    .factory('SetEnabledMsg', SetEnabledMsg)
    .controller('HostsAddController', HostsAddController)
    .controller('HostEditController', HostsEditController);
