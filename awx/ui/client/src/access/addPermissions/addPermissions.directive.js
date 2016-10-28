/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import addPermissionsController from './addPermissions.controller';

/* jshint unused: vars */
export default ['templateUrl', '$state',
    'Wait', 'addPermissionsUsersList', 'addPermissionsTeamsList',
    function(templateUrl, $state, Wait, usersList, teamsList) {
        return {
            restrict: 'E',
            scope: {
                usersDataset: '=',
                teamsDataset: '=',
                resourceData: '=',
            },
            controller: addPermissionsController,
            templateUrl: templateUrl('access/addPermissions/addPermissions'),
            link: function(scope, element, attrs) {
                scope.toggleFormTabs('users');
                $('#add-permissions-modal').modal('show');

                scope.closeModal = function() {
                    $state.go('^', null, {reload: true});
                };

                window.scrollTo(0, 0);
            }
        };
    }
];
