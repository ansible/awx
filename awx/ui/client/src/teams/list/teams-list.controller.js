/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'Rest', 'TeamList', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'Wait', '$state', '$filter',
    'rbacUiControlService', 'Dataset', 'resolvedModels', 'i18n',
    function($scope, Rest, TeamList, Prompt, ProcessErrors,
    GetBasePath, Wait, $state, $filter, rbacUiControlService, Dataset, models, i18n) {

        const { me } = models;
        var list = TeamList,
            defaultUrl = GetBasePath('teams');

        init();

        function init() {
            $scope.canEdit = me.get('summary_fields.user_capabilities.edit');
            $scope.canAdd = false;

            rbacUiControlService.canAdd('teams')
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                });
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.selected = [];
        }

        $scope.addTeam = function() {
            $state.go('teams.add');
        };

        $scope.editTeam = function(id) {
            $state.go('teams.edit', { team_id: id });
        };

        $scope.deleteTeam = function(id, name) {

            var action = function() {
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .then(() => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');

                        let reloadListStateParams = null;

                        if($scope.teams.length === 1 && $state.params.team_search && _.has($state, 'params.team_search.page') && $state.params.team_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.team_search.page = (parseInt(reloadListStateParams.team_search.page)-1).toString();
                        }

                        if (parseInt($state.params.team_id) === id) {
                            $state.go('^', reloadListStateParams, { reload: true });
                        } else {
                            $state.go('.', reloadListStateParams, { reload: true });
                        }
                    })
                    .catch(({data, status}) => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                resourceName: $filter('sanitize')(name),
                body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete this team?') + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };
    }
];
