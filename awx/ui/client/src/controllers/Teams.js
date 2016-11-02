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

export function TeamsList($scope, $rootScope, $log, $stateParams,
    Rest, Alert, TeamList, Prompt, ClearScope, ProcessErrors,
    GetBasePath, Wait, $state, $filter, rbacUiControlService, Dataset) {

    ClearScope();

    var list = TeamList,
        defaultUrl = GetBasePath('teams');

    init();

    function init() {
        $scope.canAdd = false;

        rbacUiControlService.canAdd('teams')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        _.forEach($scope[list.name], (team) => {
            team.organization_name = team.summary_fields.organization.name;
        });

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
                .success(function() {
                    Wait('stop');
                    $('#prompt-modal').modal('hide');
                    if (parseInt($state.params.team_id) === id) {
                        $state.go('^', null, { reload: true });
                    } else {
                        $state.go('.', null, { reload: true });
                    }
                })
                .error(function(data, status) {
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
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the team below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };
}


TeamsList.$inject = ['$scope', '$rootScope', '$log',
    '$stateParams', 'Rest', 'Alert', 'TeamList', 'Prompt', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'Wait', '$state', '$filter', 'rbacUiControlService', 'Dataset'
];


export function TeamsAdd($scope, $rootScope, $stateParams, TeamForm, GenerateForm, Rest, Alert, ProcessErrors,
    ClearScope, GetBasePath, Wait, $state) {
    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //$scope.

    Rest.setUrl(GetBasePath('teams'));
    Rest.options()
        .success(function(data) {
            if (!data.actions.POST) {
                $state.go("^");
                Alert('Permission Error', 'You do not have permission to add a team.', 'alert-info');
            }
        });

    // Inject dynamic view
    var defaultUrl = GetBasePath('teams'),
        form = TeamForm;

    init();

    function init() {
        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope);

        $rootScope.flashMessage = null;
    }

    // Save
    $scope.formSave = function() {
        var fld, data;
        GenerateForm.clearApiErrors($scope);
        Wait('start');
        Rest.setUrl(defaultUrl);
        data = {};
        for (fld in form.fields) {
            data[fld] = $scope[fld];
        }
        Rest.post(data)
            .success(function(data) {
                Wait('stop');
                $rootScope.flashMessage = "New team successfully created!";
                $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                $state.go('teams.edit', { team_id: data.id }, { reload: true });
            })
            .error(function(data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to add new team. Post returned status: ' +
                        status
                });
            });
    };

    $scope.formCancel = function() {
        $state.go('teams');
    };
}

TeamsAdd.$inject = ['$scope', '$rootScope', '$stateParams', 'TeamForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'ClearScope', 'GetBasePath', 'Wait', '$state'
];


export function TeamsEdit($scope, $rootScope, $stateParams,
    TeamForm, Rest, ProcessErrors, ClearScope, GetBasePath, Wait, $state) {

    ClearScope();

    var form = TeamForm,
        id = $stateParams.team_id,
        defaultUrl = GetBasePath('teams') + id;

    init();

    function init() {
        $scope.team_id = id;
        Rest.setUrl(defaultUrl);
        Wait('start');
        Rest.get(defaultUrl).success(function(data) {
            setScopeFields(data);
            $scope.organization_name = data.summary_fields.organization.name;

            $scope.team_obj = data;
        });

        $scope.$watch('team_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });


    }

    // @issue I think all this really want to do is _.forEach(form.fields, (field) =>{ $scope[field] = data[field]})
    function setScopeFields(data) {
        _(data)
            .pick(function(value, key) {
                return form.fields.hasOwnProperty(key) === true;
            })
            .forEach(function(value, key) {
                $scope[key] = value;
            })
            .value();
        return;
    }

    // prepares a data payload for a PUT request to the API
    function processNewData(fields) {
        var data = {};
        _.forEach(fields, function(value, key) {
            if ($scope[key] !== '' && $scope[key] !== null && $scope[key] !== undefined) {
                data[key] = $scope[key];
            }
        });
        return data;
    }

    $scope.formCancel = function() {
        $state.go('teams', null, { reload: true });
    };

    $scope.formSave = function() {
        $rootScope.flashMessage = null;
        if ($scope[form.name + '_form'].$valid) {
            var data = processNewData(form.fields);
            Rest.put(data).success(function() {
                    $state.go($state.current, null, { reload: true });
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve user: ' +
                            $stateParams.id + '. GET status: ' + status
                    });
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
}

TeamsEdit.$inject = ['$scope', '$rootScope', '$stateParams', 'TeamForm', 'Rest',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'Wait', '$state'
];
