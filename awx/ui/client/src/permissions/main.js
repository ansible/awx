/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import permissionsList from './permissions-list/main';
import permissionsAdd from './permissions-add/main';
import permissionsEdit from './permissions-edit/main';
import list from './permissions-list';
import form from './permissions-form';
import permissionsCategoryChange from './permissions-category-change.factory';
import permissionsLabel from './permissions-labels.factory';

export default
    angular.module('permissions', [
            permissionsList.name,
            permissionsAdd.name,
            permissionsEdit.name
        ])
        .factory('permissionsList', list)
        .factory('permissionsForm', form)
        .factory('permissionsCategoryChange', permissionsCategoryChange)
        .factory('permissionsLabel', permissionsLabel);
