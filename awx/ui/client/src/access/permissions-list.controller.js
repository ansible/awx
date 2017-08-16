/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'ListDefinition', 'Dataset', 'Wait', 'Rest', 'ProcessErrors', 'Prompt', '$state', '$filter',
    function($scope, list, Dataset, Wait, Rest, ProcessErrors, Prompt, $state, $filter) {
        init();

        function init() {
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[`${list.iterator}s`] = $scope[`${list.iterator}_dataset`].results;
        }

        $scope.deletePermissionFromUser = function(userId, userName, roleName, roleType, url) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": Number(userId) })
                    .success(function() {
                        Wait('stop');
                        $state.go('.', null, {reload: true});
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Could not disassociate user from role.  Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: `Remove role`,
                body: `
                    <div class="Prompt-bodyQuery">
                        Confirm  the removal of the ${$filter('sanitize')(roleType)}
                            <span class="Prompt-emphasis"> ${roleName} </span>
                        role associated with ${$filter('sanitize')(userName)}.
                    </div>
                `,
                action: action,
                actionText: 'REMOVE'
            });
        };

        $scope.deletePermissionFromTeam = function(teamId, teamName, roleName, roleType, url) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": teamId })
                    .success(function() {
                        Wait('stop');
                        $state.go('.', null, {reload: true});
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Could not disassociate team from role.  Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: `Remove role`,
                body: `
                    <div class="Prompt-bodyQuery">
                        Confirm  the removal of the ${$filter('sanitize')(roleType)}
                            <span class="Prompt-emphasis"> ${roleName} </span>
                        role associated with the ${$filter('sanitize')(teamName)} team.
                    </div>
                `,
                action: action,
                actionText: 'REMOVE'
            });
        };
    }
];
