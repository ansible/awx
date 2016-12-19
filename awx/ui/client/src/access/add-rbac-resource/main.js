/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addRbacResourceDirective from './rbac-resource.directive';
import rbacMultiselect from '../rbac-multiselect/main';

export default
    angular.module('AddRbacResourceModule', [rbacMultiselect.name])
        .directive('addRbacResource', addRbacResourceDirective);
