/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildHostAddState from './build-host-add-state.factory';
import controller from './host-add.controller';

export default
angular.module('relatedHostsAdd', [])
    .factory('buildHostAddState', buildHostAddState)
    .controller('RelatedHostAddController', controller);
