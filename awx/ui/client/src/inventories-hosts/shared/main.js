/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import SetStatus from './factories/set-status.factory';
import SetEnabledMsg from './factories/set-enabled-msg.factory';
import ansibleFacts from './ansible-facts/main';
import InventoriesService from './inventories.service';
import GroupsService from './groups.service';
import HostsService from './hosts.service';
import associateGroups from './associate-groups/associate-groups.directive';
import associateHosts from './associate-hosts/associate-hosts.directive';

export default
angular.module('inventoriesHostsFactories', [
    ansibleFacts.name
])
    .factory('SetStatus', SetStatus)
    .factory('SetEnabledMsg', SetEnabledMsg)
    .service('HostsService', HostsService)
    .service('InventoriesService', InventoriesService)
    .service('GroupsService', GroupsService)
    .directive('associateGroups', associateGroups)
    .directive('associateHosts', associateHosts);
