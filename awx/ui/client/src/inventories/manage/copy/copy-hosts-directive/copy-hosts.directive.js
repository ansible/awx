/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import copyHostsDirectiveController from './copy-hosts.directive.controller';

export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'EA',
            scope: true,
            replace: true,
            templateUrl: templateUrl('inventories/manage/copy/copy-hosts-directive/copy-hosts.directive'),
            link: function(scope, element, attrs) {

            },
            controller: copyHostsDirectiveController,
            controllerAs: 'vm',
            bindToController: true
        };
    }
];
