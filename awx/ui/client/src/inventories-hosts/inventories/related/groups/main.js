/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import groupList from './list/main';
import groupAdd from './add/main';
import groupEdit from './edit/main';
import groupFormDefinition from './groups.form';
import groupListDefinition from './groups.list';
import nestedGroups from './related/nested-groups/main';
import nestedHosts from './related/nested-hosts/main';

export default
    angular.module('group', [
        groupList.name,
        groupAdd.name,
        groupEdit.name,
        nestedGroups.name,
        nestedHosts.name
    ])
    .factory('GroupForm', groupFormDefinition)
    .factory('GroupList', groupListDefinition);
