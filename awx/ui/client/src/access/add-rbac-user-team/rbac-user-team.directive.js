/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import controller from './rbac-user-team.controller';

/* jshint unused: vars */
export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'E',
            scope: {
                resolve: "="
            },
            controller: controller,
            controllerAs: 'rbac',
            templateUrl: templateUrl('access/add-rbac-user-team/rbac-user-team'),
            link: function(scope, element, attrs) {
                $('#add-permissions-modal').modal('show');
                window.scrollTo(0, 0);
            }
        };
    }
];
