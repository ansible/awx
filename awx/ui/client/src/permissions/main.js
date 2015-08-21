/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import permissionsList from './list/main';
import permissionsAdd from './add/main';
import permissionsEdit from './edit/main';

import list from './shared/permissions.list';
import form from './shared/permissions.form';

import permissionsCategoryChange from './shared/category-change.factory';
import permissionsChoices from './shared/get-choices.factory';
import permissionsLabel from './shared/get-labels.factory';
import permissionsSearchSelect from './shared/get-search-select.factory';

export default
    angular.module('permissions', [
            permissionsList.name,
            permissionsAdd.name,
            permissionsEdit.name
        ])
        .factory('permissionsList', list)
        .factory('permissionsForm', form)
        .factory('permissionsCategoryChange', permissionsCategoryChange)
        .factory('permissionsChoices', permissionsChoices)
        .factory('permissionsLabel', permissionsLabel)
        .factory('permissionsSearchSelect', permissionsSearchSelect);
