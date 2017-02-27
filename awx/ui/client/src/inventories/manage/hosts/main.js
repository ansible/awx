/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import HostsAddController from './hosts-add.controller';
import HostsEditController from './hosts-edit.controller';

export default
angular.module('manageHosts', [])
    .controller('HostsAddController', HostsAddController)
    .controller('HostEditController', HostsEditController);
