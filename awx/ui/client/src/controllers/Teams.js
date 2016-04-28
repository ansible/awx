/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Teams
 * @description This controller's for teams
*/


export function TeamsList($scope, $rootScope, $location, $log, $stateParams,
    Rest, Alert, TeamList, GenerateList, Prompt, SearchInit, PaginateInit,
    ReturnToCaller, ClearScope, ProcessErrors, SetTeamListeners, GetBasePath,
    SelectionInit, Wait, $state, Refresh) {

    ClearScope();

    var list = TeamList,
        defaultUrl = GetBasePath('teams'),
        generator = GenerateList,
        paths = $location.path().replace(/^\//, '').split('/'),
        mode = (paths[0] === 'teams') ? 'edit' : 'select',
        url;

    var injectForm = function() {
        generator.inject(list, { mode: mode, scope: $scope });
    };

    injectForm();

    $scope.$on("RefreshTeamsList", function() {
        injectForm();
        Refresh({
            scope: $scope,
            set: 'teams',
            iterator: 'team',
            url: GetBasePath('teams') + "?order_by=name&page_size=" + $scope.team_page_size
        });
    });

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

    $scope.addTeam = function () {
        $state.transitionTo('teams.add');
    };

    $scope.editTeam = function (id) {
        $state.transitionTo('teams.edit', {team_id: id});
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
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the team below?</div><div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };
}

TeamsList.$inject = ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'TeamList', 'generateList', 'Prompt',
    'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'SetTeamListeners', 'GetBasePath', 'SelectionInit', 'Wait',
    '$state', 'Refresh'
];


export function TeamsAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, TeamForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, GenerateList, OrganizationList, SearchInit,
    PaginateInit, GetBasePath, LookUpInit, Wait, $state) {
    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //$scope.

    // Inject dynamic view
    var defaultUrl = GetBasePath('teams'),
        form = TeamForm,
        generator = GenerateForm,
        scope = generator.inject(form, { mode: 'add', related: false });

    $rootScope.flashMessage = null;
    generator.reset();

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
                $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                $state.go('teams.edit', {team_id: data.id}, {reload: true});
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to add new team. Post returned status: ' +
                    status });
            });
    };

    $scope.formCancel = function () {
        $state.transitionTo('teams');
    };
}

TeamsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'TeamForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'generateList',
    'OrganizationList', 'SearchInit', 'PaginateInit', 'GetBasePath',
    'LookUpInit', 'Wait', '$state'
];


export function TeamsEdit($scope, $rootScope, $location,
    $stateParams, TeamForm, GenerateForm, Rest, ProcessErrors,
    RelatedSearchInit, RelatedPaginateInit, ClearScope,
    LookUpInit, GetBasePath, OrganizationList, Wait, $state) {

    ClearScope();

    var defaultUrl = GetBasePath('teams'),
        generator = GenerateForm,
        form = TeamForm,
        id = $stateParams.team_id,
        relatedSets = {},
        set;

    $scope.team_id = id;


    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();

    var setScopeFields = function(data){
        _(data)
        .pick(function(value, key){
            return form.fields.hasOwnProperty(key) === true;
        })
        .forEach(function(value, key){
            $scope[key] = value;
        })
        .value();
        return;
    };
    var setScopeRelated = function(data, related){
        _(related)
        .pick(function(value, key){
            return data.related.hasOwnProperty(key) === true;
        })
        .forEach(function(value, key){
            relatedSets[key] = {
                url: data.related[key],
                iterator: value.iterator
            };
        })
        .value();
    };

    // prepares a data payload for a PUT request to the API
    var processNewData = function(fields){
        var data = {};
        _.forEach(fields, function(value, key){
            if ($scope[key] !== '' && $scope[key]  !== null && $scope[key] !== undefined){
             data[key] = $scope[key];
            }
        });
        return data;
    };

    var init = function(){
        var url = defaultUrl + id;
        Rest.setUrl(url);
        Wait('start');
        Rest.get(url).success(function(data){
            setScopeFields(data);
            setScopeRelated(data, form.related);
            $scope.organization_name = data.summary_fields.organization.name;

            RelatedSearchInit({
                scope: $scope,
                form: form,
                relatedSets: relatedSets
            });

            RelatedPaginateInit({
                scope: $scope,
                relatedSets: relatedSets
            });

            for (set in relatedSets) {
                $scope.search(relatedSets[set].iterator);
            }

            $scope.team_obj = data;

            LookUpInit({
                url: GetBasePath('organizations'),
                scope: $scope,
                form: form,
                current_item: $scope.organization,
                list: OrganizationList,
                field: 'organization',
                input_type: 'radio'
            });
        });
    };

    $scope.formCancel = function(){
        $state.go('teams', null, {reload: true});
    };

    $scope.formSave = function(){
        generator.clearApiErrors();
        generator.checkAutoFill();
        $rootScope.flashMessage = null;
        if ($scope[form.name + '_form'].$valid){
            Rest.setUrl(defaultUrl + id + '/');
            var data = processNewData(form.fields);
            Rest.put(data).success(function(){
                $state.go('teams', null, {reload: true});
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve user: ' +
                $stateParams.id + '. GET status: ' + status });
            });
        }
    };

    init();

    $scope.convertApiUrl = function(str) {
        if (str) {
            return str.replace("api/v1", "#");
        } else {
            return null;
        }
    };

    /* Related Set implementation TDB */
}

TeamsEdit.$inject = ['$scope', '$rootScope',  '$location',
    '$stateParams', 'TeamForm', 'GenerateForm', 'Rest',
    'ProcessErrors', 'RelatedSearchInit', 'RelatedPaginateInit',
     'ClearScope', 'LookUpInit', 'GetBasePath',
     'OrganizationList', 'Wait', '$state'
];
