/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import relatedHostAdd from './add/main';
 import relatedHostEdit from './edit/main';
 import relatedHostList from './list/main';
 import relatedHostsListDefinition from './related-host.list';
 import relatedHostsFormDefinition from './related-host.form';
 // import HostManageService from './hosts.service';
 // import SetStatus from './set-status.factory';
 // import SetEnabledMsg from './set-enabled-msg.factory';
 // import SmartInventory from './smart-inventory/main';

export default
angular.module('relatedHost', [
        relatedHostAdd.name,
        relatedHostEdit.name,
        relatedHostList.name
    ])
    .value('RelatedHostsFormDefinition', relatedHostsFormDefinition)
    .value('RelatedHostsListDefinition', relatedHostsListDefinition);
    // .factory('SetStatus', SetStatus)
    // .factory('SetEnabledMsg', SetEnabledMsg)
    // .service('HostManageService', HostManageService);
