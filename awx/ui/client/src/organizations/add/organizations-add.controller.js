/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'OrganizationForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait',
    '$state',
    function($scope, $rootScope, $compile, $location, $log,
        $stateParams, OrganizationForm, GenerateForm, Rest, Alert, ProcessErrors,
        ClearScope, GetBasePath, ReturnToCaller, Wait, $state) {

        ClearScope();

        // Inject dynamic view
        var generator = GenerateForm,
            form = OrganizationForm(),
            base = $location.path().replace(/^\//, '').split('/')[0];

        generator.inject(form, {
            mode: 'add',
            related: false,
            scope: $scope
        });
        generator.reset();

        $scope.$emit("HideOrgListHeader");

        // Save
        $scope.formSave = function() {
            generator.clearApiErrors();
            Wait('start');
            var url = GetBasePath(base);
            url += (base !== 'organizations') ? $stateParams.project_id + '/organizations/' : '';
            Rest.setUrl(url);
            Rest.post({
                    name: $scope.name,
                    description: $scope.description
                })
                .success(function(data) {
                    Wait('stop');
                    $scope.$emit("ReloadOrganzationCards", data.id);
                    if (base === 'organizations') {
                        $rootScope.flashMessage = "New organization successfully created!";
                        $location.path('/organizations/' + data.id);
                    } else {
                        ReturnToCaller(1);
                    }
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new organization. Post returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $scope.$emit("ReloadOrganzationCards");
            $scope.$emit("ShowOrgListHeader");
            $state.transitionTo('organizations');
        };
    }
];
