/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Teams.js
 *
 *  Controller functions for the Team model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Teams
 * @description This controller's for teams
*/


export function TeamsList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, TeamList, GenerateList, LoadBreadCrumbs,
    Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, SetTeamListeners, GetBasePath, SelectionInit, Wait,
    Stream) {

    ClearScope();

    var list = TeamList,
        defaultUrl = GetBasePath('teams'),
        generator = GenerateList,
        paths = $location.path().replace(/^\//, '').split('/'),
        mode = (paths[0] === 'teams') ? 'edit' : 'select',
        url;

    generator.inject(list, { mode: mode, scope: $scope });
    $scope.selected = [];

    url = GetBasePath('base') + $location.path() + '/';
    SelectionInit({
        scope: $scope,
        list: list,
        url: url,
        returnToCaller: 1
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
        url: defaultUrl
    });
    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });
    $scope.search(list.iterator);

    LoadBreadCrumbs();

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    $scope.addTeam = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editTeam = function (id) {
        $location.path($location.path() + '/' + id);
    };

    $scope.deleteTeam = function (id, name) {

        var action = function () {
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    Wait('stop');
                    $('#prompt-modal').modal('hide');
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    Wait('stop');
                    $('#prompt-modal').modal('hide');
                    ProcessErrors($scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class=\"alert alert-info\">Delete team ' + name + '?</div>',
            action: action
        });
    };
}

TeamsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'TeamList', 'generateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'SetTeamListeners', 'GetBasePath', 'SelectionInit', 'Wait', 'Stream'
];


export function TeamsAdd($scope, $rootScope, $compile, $location, $log, $routeParams, TeamForm, GenerateForm,
    Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GenerateList,
    OrganizationList, SearchInit, PaginateInit, GetBasePath, LookUpInit, Wait) {
    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //$scope.

    // Inject dynamic view
    var defaultUrl = GetBasePath('teams'),
        form = TeamForm,
        generator = GenerateForm,
        scope = generator.inject(form, { mode: 'add', related: false });

    $rootScope.flashMessage = null;
    generator.reset();
    LoadBreadCrumbs();

    LookUpInit({
        scope: $scope,
        form: form,
        current_item: null,
        list: OrganizationList,
        field: 'organization',
        input_type: 'radio'
    });

    // Save
    $scope.formSave = function () {
        var fld, data;
        generator.clearApiErrors();
        Wait('start');
        Rest.setUrl(defaultUrl);
        data = {};
        for (fld in form.fields) {
            data[fld] = scope[fld];
        }
        Rest.post(data)
            .success(function (data) {
                Wait('stop');
                $rootScope.flashMessage = "New team successfully created!";
                $location.path('/teams/' + data.id);
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to add new team. Post returned status: ' +
                    status });
            });
    };

    // Reset
    $scope.formReset = function () {
        // Defaults
        generator.reset();
    };
}

TeamsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'TeamForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'generateList',
    'OrganizationList', 'SearchInit', 'PaginateInit', 'GetBasePath', 'LookUpInit', 'Wait'
];


export function TeamsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, TeamForm, GenerateForm, Rest, Alert, ProcessErrors,
    LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInit, Prompt, GetBasePath, CheckAccess,
    OrganizationList, Wait, Stream) {

    ClearScope();

    var defaultUrl = GetBasePath('teams'),
        generator = GenerateForm,
        form = TeamForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $routeParams.team_id,
        relatedSets = {};

    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();

    $scope.PermissionAddAllowed = false;

    // Retrieve each related set and any lookups
    if ($scope.teamLoadedRemove) {
        $scope.teamLoadedRemove();
    }
    $scope.teamLoadedRemove = $scope.$on('teamLoaded', function () {
        CheckAccess({ scope: $scope });
        if ($scope.organization_url) {
            Rest.setUrl($scope.organization_url);
            Rest.get()
                .success(function (data) {
                    $scope.organization_name = data.name;
                    master.organization_name = data.name;
                    Wait('stop');
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve organization: ' +
                        $scope.orgnization_url + '. GET status: ' + status });
                });
            for (var set in relatedSets) {
                $scope.search(relatedSets[set].iterator);
            }
        } else {
            $scope.organization_name = "";
            master.organization_name = "";
            Wait('stop');
        }
    });

    // Retrieve detail record and prepopulate the form
    Wait('start');
    Rest.setUrl(defaultUrl + ':id/');
    Rest.get({
        params: {
            id: id
        }
    })
        .success(function (data) {
            var fld, related, set;
            LoadBreadCrumbs({ path: '/teams/' + id, title: data.name });
            for (fld in form.fields) {
                if (data[fld]) {
                    $scope[fld] = data[fld];
                    master[fld] = $scope[fld];
                }
            }
            related = data.related;
            for (set in form.related) {
                if (related[set]) {
                    relatedSets[set] = {
                        url: related[set],
                        iterator: form.related[set].iterator
                    };
                }
            }
            // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
            RelatedSearchInit({
                scope: $scope,
                form: form,
                relatedSets: relatedSets
            });
            RelatedPaginateInit({
                scope: $scope,
                relatedSets: relatedSets
            });

            LookUpInit({
                scope: $scope,
                form: form,
                current_item: data.organization,
                list: OrganizationList,
                field: 'organization',
                input_type: 'radio'
            });

            $scope.organization_url = data.related.organization;
            $scope.$emit('teamLoaded');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to retrieve team: ' + $routeParams.team_id +
                '. GET status: ' + status });
        });

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    // Save changes to the parent
    $scope.formSave = function () {
        var data = {}, fld;
        generator.clearApiErrors();
        Wait('start');
        $rootScope.flashMessage = null;
        Rest.setUrl(defaultUrl + $routeParams.team_id + '/');
        for (fld in form.fields) {
            data[fld] = $scope[fld];
        }
        Rest.put(data)
            .success(function () {
                Wait('stop');
                var base = $location.path().replace(/^\//, '').split('/')[0];
                if (base === 'teams') {
                    ReturnToCaller();
                }
                else {
                    ReturnToCaller(1);
                }
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to update team: ' + $routeParams.team_id + '. PUT status: ' + status });
            });
    };

    // Cancel
    $scope.formReset = function () {
        $rootScope.flashMessage = null;
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        if (set === 'permissions') {
            if ($scope.PermissionAddAllowed) {
                $location.path('/' + base + '/' + $routeParams.team_id + '/' + set + '/add');
            } else {
                Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
            }
        } else {
            $location.path('/' + base + '/' + $routeParams.team_id + '/' + set);
        }
    };

    // Related set: Edit button
    $scope.edit = function (set, id) {
        $rootScope.flashMessage = null;
        if (set === 'permissions') {
            $location.path('/' + base + '/' + $routeParams.team_id + '/' + set + '/' + id);
        } else {
            $location.path('/' + set + '/' + id);
        }
    };

    // Related set: Delete button
    $scope['delete'] = function (set, itm_id, name, title) {
        $rootScope.flashMessage = null;

        var action = function () {
            var url;
            if (set === 'permissions') {
                if ($scope.PermissionAddAllowed) {
                    url = GetBasePath('base') + 'permissions/' + itm_id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            $('#prompt-modal').modal('hide');
                            $scope.search(form.related[set].iterator);
                        })
                        .error(function (data, status) {
                            $('#prompt-modal').modal('hide');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                                ' failed. DELETE returned status: ' + status });
                        });
                } else {
                    Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
                }
            } else {
                url = defaultUrl + $routeParams.team_id + '/' + set + '/';
                Rest.setUrl(url);
                Rest.post({ id: itm_id, disassociate: 1 })
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        $scope.search(form.related[set].iterator);
                    })
                    .error(function (data, status) {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            ' failed. POST returned status: ' + status });
                    });
            }
        };

        Prompt({
            hdr: 'Delete',
            body: 'Are you sure you want to remove ' + name + ' from ' + $scope.name + ' ' + title + '?',
            action: action
        });
    };
}

TeamsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'TeamForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt', 'GetBasePath', 'CheckAccess', 'OrganizationList', 'Wait', 'Stream'
];
