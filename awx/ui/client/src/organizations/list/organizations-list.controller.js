/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', '$rootScope', '$location',
    '$log', '$compile', 'Rest', 'PaginateWidget', 'PaginateInit',
    'SearchInit', 'OrganizationList', 'Alert', 'Prompt', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'Wait',
    '$state',
    function($stateParams, $scope, $rootScope, $location,
        $log, $compile, Rest, PaginateWidget, PaginateInit,
        SearchInit, OrganizationList, Alert, Prompt, ClearScope,
        ProcessErrors, GetBasePath, Wait,
        $state) {

        ClearScope();

        var defaultUrl = GetBasePath('organizations'),
            list = OrganizationList,
            pageSize = $scope.orgCount;

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
        });

        $scope.search(list.iterator);

        $scope.PaginateWidget = PaginateWidget({
            iterator: list.iterator,
            set: 'organizations'
        });

        var paginationContainer = $('#pagination-container');
        paginationContainer.html($scope.PaginateWidget);
        $compile(paginationContainer.contents())($scope)

        var parseCardData = function(cards) {
            return cards.map(function(card) {
                var val = {};
                val.name = card.name;
                val.id = card.id;
                if (card.id + "" === cards.activeCard) {
                    val.isActiveCard = true;
                }
                val.description = card.description || undefined;
                val.links = [];
                val.links.push({
                    href: card.related.users,
                    name: "USERS",
                    count: card.summary_fields.related_field_counts.users
                });
                val.links.push({
                    href: card.related.teams,
                    name: "TEAMS",
                    count: card.summary_fields.related_field_counts.teams
                });
                val.links.push({
                    href: card.related.inventories,
                    name: "INVENTORIES",
                    count: card.summary_fields.related_field_counts.inventories
                });
                val.links.push({
                    href: card.related.projects,
                    name: "PROJECTS",
                    count: card.summary_fields.related_field_counts.projects
                });
                val.links.push({
                    href: card.related.job_templates,
                    name: "JOB TEMPLATES",
                    count: card.summary_fields.related_field_counts.job_templates
                });
                val.links.push({
                    href: card.related.admins,
                    name: "ADMINS",
                    count: card.summary_fields.related_field_counts.admins
                });
                return val;
            });
        };

        var getOrganization = function(id) {
            Rest.setUrl(defaultUrl);
            Rest.get()
                .success(function(data) {
                    data.results.activeCard = id;
                    $scope.orgCount = data.count;
                    $scope.orgCards = parseCardData(data.results);
                    Wait("stop");
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Call to ' + defaultUrl + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        $scope.$on("ReloadOrgListView", function() {
            if ($state.$current.self.name === "organizations") {
                delete $scope.activeCard;
                if ($scope.orgCards) {
                    $scope.orgCards = $scope.orgCards.map(function(card) {
                        delete card.isActiveCard;
                        return card;
                    });
                }
                $scope.hideListHeader = false;
            }
        });

        $scope.$on("ReloadOrganzationCards", function(e, id) {
            $scope.activeCard = id;
            getOrganization(id);
        });

        $scope.$on("HideOrgListHeader", function() {
            $scope.hideListHeader = true;
        });

        $scope.$on("ShowOrgListHeader", function() {
            $scope.hideListHeader = false;
        });

        getOrganization();

        $rootScope.flashMessage = null;

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
                        if ($state.current.name !== "organzations") {
                            $state.transitionTo("organizations");
                        }
                        $scope.$emit("ReloadOrganzationCards");
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
    }
]
