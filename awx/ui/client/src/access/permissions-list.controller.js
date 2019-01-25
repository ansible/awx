/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'ListDefinition', 'Dataset', 'Wait', 'Rest', 'ProcessErrors', 'Prompt', '$state', '$filter', 'i18n',
    function($scope, list, Dataset, Wait, Rest, ProcessErrors, Prompt, $state, $filter, i18n) {
        init();

        function init() {
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[`${list.iterator}s`] = $scope[`${list.iterator}_dataset`].results;
        }

        let reloadAfterDelete = () => {
            let reloadListStateParams = null;

            if($scope.permissions.length === 1 && $state.params.permission_search && _.has($state, 'params.permission_search.page') && parseInt($state.params.permission_search.page).toString() !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                reloadListStateParams.permission_search.page = (parseInt(reloadListStateParams.permission_search.page)-1).toString();
            }

            $state.go('.', reloadListStateParams, {reload: true});
        };

        $scope.deletePermissionFromUser = function(userId, userName, roleName, roleType, url) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": Number(userId) })
                    .then(() => {
                        Wait('stop');
                        reloadAfterDelete();
                    })
                    .catch(({data, status}) => {
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
                actionText: i18n._('REMOVE')
            });
        };

        $scope.deletePermissionFromTeam = function(teamId, teamName, roleName, roleType, url) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": teamId })
                    .then(() => {
                        Wait('stop');
                        reloadAfterDelete();
                    })
                    .catch(({data, status}) => {
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
                actionText: i18n._('REMOVE')
            });
        };
    }
];
