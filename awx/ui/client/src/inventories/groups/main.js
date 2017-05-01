/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import groupList from './list/main';
import groupAdd from './add/main';
import groupEdit from './edit/main';
import nestedGroups from './nested-groups/main';
import nestedHosts from './nested-hosts/main';
import groupFormDefinition from './groups.form';
import groupListDefinition from './groups.list';
import service from './groups.service';
import GetHostsStatusMsg from './factories/get-hosts-status-msg.factory';

export default
    angular.module('group', [
        groupList.name,
        groupAdd.name,
        groupEdit.name,
        nestedGroups.name,
        nestedHosts.name
    ])
    .factory('GroupForm', groupFormDefinition)
    .value('GroupList', groupListDefinition)
    .factory('GetHostsStatusMsg', GetHostsStatusMsg)
    .service('GroupManageService', service);
