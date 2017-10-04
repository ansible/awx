/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', 'TeamForm', 'GenerateForm', 'Rest',
    'Alert', 'ProcessErrors', 'GetBasePath', 'Wait',  '$state',
    function($scope, $rootScope, TeamForm, GenerateForm, Rest, Alert,
    ProcessErrors, GetBasePath, Wait, $state) {

        Rest.setUrl(GetBasePath('teams'));
        Rest.options()
            .then(({data}) => {
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
            $scope.canEditOrg = true;
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
                .then(({data}) => {
                    Wait('stop');
                    $rootScope.flashMessage = "New team successfully created!";
                    $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                    $state.go('teams.edit', { team_id: data.id }, { reload: true });
                })
                .catch(({data, status}) => {
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
];
