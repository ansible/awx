/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
import manageHostsController from './manage-hosts.controller';

export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'EA',
            scope: true,
            replace: true,
            templateUrl: templateUrl('inventories/manage/manage-hosts/manage-hosts'),
            link: function(scope, element, attrs) {

            },
    //        controller: manageHostsController,
    //        controllerAs: 'vm',
    //        bindToController: true
        };
    }
];
