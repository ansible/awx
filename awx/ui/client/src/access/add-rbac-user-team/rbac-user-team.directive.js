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
                resolve: "=",
                title: "@",
            },
            controller: controller,
            templateUrl: templateUrl('access/add-rbac-user-team/rbac-user-team'),
            link: function(scope, element, attrs) {
                scope.selectTab('job_templates');
                $('#add-permissions-modal').modal('show');
                window.scrollTo(0, 0);
            }
        };
    }
];
