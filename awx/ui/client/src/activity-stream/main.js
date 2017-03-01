/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import activityStreamRoute from './activitystream.route';
import activityStreamController from './activitystream.controller';
import streamDropdownNav from './streamDropdownNav/stream-dropdown-nav.directive';
import streamDetailModal from './streamDetailModal/main';
import BuildAnchor from './factories/build-anchor.factory';
import BuildDescription from './factories/build-description.factory';
import ShowDetail from './factories/show-detail.factory';
import Stream from './factories/stream.factory';

export default angular.module('activityStream', [streamDetailModal.name])
    .controller('activityStreamController', activityStreamController)
    .directive('streamDropdownNav', streamDropdownNav)
    .factory('BuildAnchor', BuildAnchor)
    .factory('BuildDescription', BuildDescription)
    .factory('ShowDetail', ShowDetail)
    .factory('Stream', Stream)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(activityStreamRoute);
    }]);
