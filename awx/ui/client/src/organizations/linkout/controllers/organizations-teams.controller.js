/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$log', '$stateParams', 'OrgTeamList',
    'Rest', 'Alert', 'Prompt', 'OrgTeamsDataset', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'SetTeamListeners', 'GetBasePath',
    'SelectionInit', 'Wait', '$state',
    function($scope, $rootScope, $location, $log, $stateParams, OrgTeamList,
        Rest, Alert, Prompt, Dataset, ReturnToCaller, ClearScope,
        ProcessErrors, SetTeamListeners, GetBasePath,
        SelectionInit, Wait, $state) {

        var list = OrgTeamList,
            orgBase = GetBasePath('organizations');

        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.$watchCollection(list.name, function() {
                function setOrganizationName(organization) {
                    organization.organization_name = organization.summary_fields.organization.name;
                    return organization;
                }
                _.forEach($scope.teams, (team) => setOrganizationName(team));
            });

            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .success(function(data) {

                    $scope.organization_name = data.name;
                    $scope.org_id = data.id;

                    $scope.orgRelatedUrls = data.related;
                });
        }

        $scope.editTeam = function(id) {
            $state.go('teams.edit', { team_id: id });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };
    }
];
