/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import smartStatusController from './smart-status.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: {
            jobs: '=',
            templateType: '=?',
        },
        templateUrl: templateUrl('smart-status/smart-status'),
        restrict: 'E',
        controller: smartStatusController
    };
}];
