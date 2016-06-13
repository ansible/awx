/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', '$rootScope', '$location',
    '$log', '$compile', 'Rest', 'PaginateInit',
    'SearchInit', 'OrganizationList', 'Alert', 'Prompt', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'Wait',
    '$state', 'generateList',
    function($stateParams, $scope, $rootScope, $location,
        $log, $compile, Rest, PaginateInit,
        SearchInit, OrganizationList, Alert, Prompt, ClearScope,
        ProcessErrors, GetBasePath, Wait,
        $state, generateList) {

        ClearScope();

        var defaultUrl = GetBasePath('organizations'),
            list = OrganizationList,
            pageSize = 24,
            view = generateList;

        var parseCardData = function(cards) {
            return cards.map(function(card) {
                var val = {}, url = '/#/organizations/' + card.id + '/';
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
        };

        $scope.$on("ReloadOrgListView", function() {
            if ($state.$current.self.name === "organizations" ||
                $state.$current.self.name === "organizations.add") {
                $scope.activeCard = null;
            }
        });


        $scope.$watchCollection('organizations', function(value){
            $scope.orgCards = parseCardData(value);
        });

        if ($scope.removePostRefresh) {
            $scope.removePostRefresh();
        }
        $scope.removePostRefresh = $scope.$on('PostRefresh', function() {
            // Cleanup after a delete
            Wait('stop');
            $('#prompt-modal').modal('hide');
        });

        $scope.addOrganization = function() {
            $state.transitionTo('organizations.add');
        };

        $scope.editOrganization = function(id) {
            $scope.activeCard = id;
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
                        if ($state.current.name !== "organizations") {
                            if ($state.current
                                .name === 'organizations.edit' &&
                                id === parseInt($state.params
                                    .organization_id)) {
                                $state.go("organizations", {}, {reload: true});
                            } else {
                                $state.go($state.current, {}, {reload: true});
                            }
                        } else {
                            $state.go($state.current, {}, {reload: true});
                        }
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
                body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the organization below?</div><div class="Prompt-bodyTarget">' + name + '</div>',
                action: action,
                actionText: 'DELETE'
            });
        };
        var init = function(){
            // Pagination depends on html appended by list generator
            view.inject(list, {
                id: 'organizations-list',
                scope: $scope,
                mode: 'edit'
            });
            // grab the pagination elements, move, destroy list generator elements
            $('#organization-pagination').appendTo('#OrgCards');
            $('tag-search').appendTo('.OrgCards-search');
            $('#organizations-list').remove();

            PaginateInit({
                scope: $scope,
                list: list,
                url: defaultUrl,
                pageSize: pageSize,
            });
            SearchInit({
                scope: $scope,
                list: list,
                url: defaultUrl,
                set: 'organizations'
            });

            $scope.list = list;
            $rootScope.flashMessage = null;

            $scope.search(list.iterator);
            var getOrgCount = function() {
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function(data) {
                        $scope.orgCount = data.count;
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + defaultUrl + ' failed. DELETE returned status: ' + status
                        });
                    });
            };
            getOrgCount();
        };
        init();
    }
];
