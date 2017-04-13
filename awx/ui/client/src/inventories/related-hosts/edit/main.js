/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import buildHostEditState from './build-host-edit-state.factory';
import controller from './host-edit.controller';

export default
angular.module('relatedHostEdit', [])
    .factory('buildHostEditState', buildHostEditState)
    .controller('RelatedHostEditController', controller);
