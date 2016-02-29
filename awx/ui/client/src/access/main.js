/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import roleList from './roleList.directive';
import addPermissions from './addPermissions/main';

export default
    angular.module('access', [])
        .directive('roleList', roleList);
