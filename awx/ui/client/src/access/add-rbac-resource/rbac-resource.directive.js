/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import controller from './rbac-resource.controller';

/* jshint unused: vars */
export default ['templateUrl', '$state',
    'addPermissionsUsersList', 'addPermissionsTeamsList',
    function(templateUrl, $state, usersList, teamsList) {
        return {
            restrict: 'E',
            scope: {
                defaultParams: '=?',
                usersDataset: '=',
                teamsDataset: '=',
                resourceData: '=',
                withoutTeamPermissions: '@',
                onlyMemberRole: '@',
                queryPrefix: '@',
                title: '@'
            },
            controller: controller,
            templateUrl: templateUrl('access/add-rbac-resource/rbac-resource'),
            link: function(scope, element, attrs) {
                scope.selectTab('users');
                $('#add-permissions-modal').modal('show');

                scope.closeModal = function() {
                    $state.go('^', null, {reload: true});
                };

                window.scrollTo(0, 0);
            }
        };
    }
];
