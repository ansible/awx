/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildHostListState from './build-host-list-state.factory';
import RelatedHostListController from './host-list.controller';

export default
angular.module('relatedHostList', [])
    .factory('buildHostListState', buildHostListState)
    .controller('RelatedHostListController', RelatedHostListController);
