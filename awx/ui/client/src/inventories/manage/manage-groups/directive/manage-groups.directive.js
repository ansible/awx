/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import manageGroupsDirectiveController from './manage-groups.directive.controller';

export default ['templateUrl', 'ParamPass',
    function(templateUrl, ParamPass) {
        return {
            restrict: 'EA',
            scope: true,
            replace: true,
            templateUrl: templateUrl('inventories/manage/manage-groups/directive/manage-groups.directive'),
            link: function(scope, element, attrs) {

            },
            controller: manageGroupsDirectiveController,
            controllerAs: 'vm',
            bindToController: true
        };
    }
];
