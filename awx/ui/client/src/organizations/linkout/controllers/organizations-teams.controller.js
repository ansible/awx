/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$log', '$stateParams',
    'Rest', 'Alert', 'TeamList', 'generateList', 'Prompt', 'SearchInit', 'PaginateInit',
    'ReturnToCaller', 'ClearScope', 'ProcessErrors', 'SetTeamListeners', 'GetBasePath',
    'SelectionInit', 'Wait', '$state', 'Refresh',
    function($scope, $rootScope, $location, $log, $stateParams,
        Rest, Alert, TeamList, GenerateList, Prompt, SearchInit, PaginateInit,
        ReturnToCaller, ClearScope, ProcessErrors, SetTeamListeners, GetBasePath,
        SelectionInit, Wait, $state, Refresh) {

        var list,
            teamUrl,
            orgBase = GetBasePath('organizations'),
            generator = GenerateList;

        // Go out and get the organization
        Rest.setUrl(orgBase + $stateParams.organization_id);
        Rest.get()
            .success(function (data) {
                // include name of item in listTitle
                var listTitle = data.name + "<div class='List-titleLockup'></div>TEAMS";

                $scope.$parent.activeCard = parseInt($stateParams.organization_id);
                $scope.$parent.activeMode = 'teams';
                $scope.organization_name = data.name;
                $scope.org_id = data.id;

                list = _.cloneDeep(TeamList);
                list.emptyListText = "This list is populated by teams added from the&nbsp;<a ui-sref='teams.add'>Teams</a>&nbsp;section";
                delete list.actions.add;
                delete list.fieldActions.delete;
                teamUrl = data.related.teams;
                list.listTitle = listTitle;
                list.basePath = teamUrl;

                $scope.orgRelatedUrls = data.related;

                generator.inject(list, { mode: 'edit', scope: $scope, cancelButton: true });
                $rootScope.flashMessage = null;

                $scope.$on("RefreshTeamsList", function() {
                    generator.inject(list, { mode: 'edit', scope: $scope, cancelButton: true });
                    Refresh({
                        scope: $scope,
                        set: 'teams',
                        iterator: 'team',
                        url: GetBasePath('teams') + "?order_by=name&page_size=" + $scope.team_page_size
                    });
                });

                if ($scope.removePostRefresh) {
                    $scope.removePostRefresh();
                }
                $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
                    // After a refresh, populate the organization name on each row
                    var i;
                    if ($scope.teams) {
                        for (i = 0; i < $scope.teams.length; i++) {
                            if ($scope.teams[i].summary_fields.organization) {
                                $scope.teams[i].organization_name = $scope.teams[i].summary_fields.organization.name;
                            }
                        }
                    }
                });

                SearchInit({
                    scope: $scope,
                    set: 'teams',
                    list: list,
                    url: teamUrl
                });
                PaginateInit({
                    scope: $scope,
                    list: list,
                    url: teamUrl
                });
                $scope.search(list.iterator);
            });

            $scope.editTeam = function (id) {
                $state.transitionTo('teams.edit', {team_id: id});
            };

            $scope.formCancel = function(){
                $state.go('organizations');
            };
    }
];
