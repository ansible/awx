/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import copyGroupsDirectiveController from './copy-groups.directive.controller';

export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'EA',
            scope: true,
            replace: true,
            templateUrl: templateUrl('inventories/manage/copy/copy-groups-directive/copy-groups.directive'),
            link: function(scope, element, attrs) {

            },
            controller: copyGroupsDirectiveController,
            controllerAs: 'vm',
            bindToController: true
        };
    }
];
