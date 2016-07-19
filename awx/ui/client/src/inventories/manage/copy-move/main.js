/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {copyMoveGroup, copyMoveHost} from './copy-move.route';

export default
angular.module('manageCopyMove', [])
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(copyMoveGroup);
        $stateExtender.addState(copyMoveHost);
    }]);
