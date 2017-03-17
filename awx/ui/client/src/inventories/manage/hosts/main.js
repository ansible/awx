/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import HostsAddController from './hosts-add.controller';
import HostsEditController from './hosts-edit.controller';
import SetStatus from './factories/set-status.factory';
import SetEnabledMsg from './factories/set-enabled-msg.factory';
import InventoryHosts from './inventory-hosts.list';

export default
angular.module('manageHosts', [])
    .factory('SetStatus', SetStatus)
    .factory('SetEnabledMsg', SetEnabledMsg)
    .value('InventoryHosts', InventoryHosts)
    .controller('HostsAddController', HostsAddController)
    .controller('HostEditController', HostsEditController);
