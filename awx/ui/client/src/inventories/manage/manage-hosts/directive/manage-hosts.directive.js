/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import manageHostsDirectiveController from './manage-hosts.directive.controller';

export default ['templateUrl', 'ParamPass',
    function(templateUrl, ParamPass) {
        return {
            restrict: 'EA',
            scope: true,
            replace: true,
            templateUrl: templateUrl('inventories/manage/manage-hosts/directive/manage-hosts.directive'),
            link: function(scope, element, attrs) {

            },
            controller: manageHostsDirectiveController,
            controllerAs: 'vm',
            bindToController: true
        };
    }
];
