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
import GetTargetTitle from './get-target-title.factory';
import ModelToBasePathKey from './model-to-base-path-key.factory';
import ActivityDetailForm from './activity-detail.form';
import StreamList from './streams.list';

export default angular.module('activityStream', [streamDetailModal.name])
    .controller('activityStreamController', activityStreamController)
    .directive('streamDropdownNav', streamDropdownNav)
    .factory('BuildAnchor', BuildAnchor)
    .factory('BuildDescription', BuildDescription)
    .factory('ShowDetail', ShowDetail)
    .factory('GetTargetTitle', GetTargetTitle)
    .factory('ModelToBasePathKey', ModelToBasePathKey)
    .factory('ActivityDetailForm', ActivityDetailForm)
    .factory('StreamList', StreamList)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(activityStreamRoute);
    }]);
