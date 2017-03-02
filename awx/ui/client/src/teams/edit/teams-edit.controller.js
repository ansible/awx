/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$stateParams', 'TeamForm', 'Rest',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'Wait', '$state',
    function($scope, $rootScope, $stateParams, TeamForm, Rest, ProcessErrors,
    ClearScope, GetBasePath, Wait, $state) {
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
                Wait('stop');
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
                Rest.setUrl(defaultUrl);
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
];
