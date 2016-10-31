/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['$stateParams', '$scope', '$rootScope', '$location',
    '$log', '$compile', 'Rest', 'OrganizationList', 'Alert', 'Prompt', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'Wait', '$state', 'rbacUiControlService', '$filter', 'Dataset',
    function($stateParams, $scope, $rootScope, $location,
        $log, $compile, Rest, OrganizationList, Alert, Prompt, ClearScope,
        ProcessErrors, GetBasePath, Wait, $state, rbacUiControlService, $filter, Dataset) {


        ClearScope();

        var defaultUrl = GetBasePath('organizations'),
            list = OrganizationList;

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("organizations")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });
            $scope.orgCount = Dataset.data.count;

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.orgCards = parseCardData($scope[list.name]);
            $rootScope.flashMessage = null;
        }

        function parseCardData(cards) {
            return cards.map(function(card) {
                var val = {},
                    url = '/#/organizations/' + card.id + '/';
                val.user_capabilities = card.summary_fields.user_capabilities;
                val.name = card.name;
                val.id = card.id;
                val.description = card.description || undefined;
                val.links = [];
                val.links.push({
                    href: url + 'users',
                    name: "USERS",
                    count: card.summary_fields.related_field_counts.users,
                    activeMode: 'users'
                });
                val.links.push({
                    href: url + 'teams',
                    name: "TEAMS",
                    count: card.summary_fields.related_field_counts.teams,
                    activeMode: 'teams'
                });
                val.links.push({
                    href: url + 'inventories',
                    name: "INVENTORIES",
                    count: card.summary_fields.related_field_counts.inventories,
                    activeMode: 'inventories'
                });
                val.links.push({
                    href: url + 'projects',
                    name: "PROJECTS",
                    count: card.summary_fields.related_field_counts.projects,
                    activeMode: 'projects'
                });
                val.links.push({
                    href: url + 'job_templates',
                    name: "JOB TEMPLATES",
                    count: card.summary_fields.related_field_counts.job_templates,
                    activeMode: 'job_templates'
                });
                val.links.push({
                    href: url + 'admins',
                    name: "ADMINS",
                    count: card.summary_fields.related_field_counts.admins,
                    activeMode: 'admins'
                });
                return val;
            });
        }

        $scope.$watchCollection(`${list.iterator}_dataset`, function(data) {
            $scope[list.name] = data.results;
            $scope.orgCards = parseCardData($scope[list.name]);
        });

        $scope.addOrganization = function() {
            $state.transitionTo('organizations.add');
        };

        $scope.editOrganization = function(id) {
            $state.transitionTo('organizations.edit', {
                organization_id: id
            });
        };

        $scope.deleteOrganization = function(id, name) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function() {
                        Wait('stop');
                        $state.reload('organizations');
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: 'Delete',
                body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the organization below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: 'DELETE'
            });
        };
    }
];
