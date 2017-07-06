/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import nestedHostsListDefinition from './group-nested-hosts.list';
import nestedHostsFormDefinition from './group-nested-hosts.form';
import controller from './group-nested-hosts-list.controller';
import addController from './group-nested-hosts-add.controller';

export default
    angular.module('nestedHosts', [])
    .factory('NestedHostsListDefinition', nestedHostsListDefinition)
    .factory('NestedHostsFormDefinition', nestedHostsFormDefinition)
    .controller('NestedHostsAddController', addController)
    .controller('NestedHostsListController', controller);
