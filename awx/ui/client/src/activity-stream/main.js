/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import activityStreamRoute from './activitystream.route';
import activityStreamController from './activitystream.controller';

import streamDropdownNav from './streamDropdownNav/stream-dropdown-nav.directive';

import streamDetailModal from './streamDetailModal/main';

export default angular.module('activityStream', [streamDetailModal.name])
    .controller('activityStreamController', activityStreamController)
    .directive('streamDropdownNav', streamDropdownNav)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(activityStreamRoute);
    }]);
