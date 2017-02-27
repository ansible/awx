/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams',
    'OrganizationForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'Wait','$state',
    function($scope, $rootScope, $location, $stateParams, OrganizationForm,
        GenerateForm, Rest, Alert, ProcessErrors,
        ClearScope, GetBasePath, Wait, $state) {

        Rest.setUrl(GetBasePath('organizations'));
        Rest.options()
            .success(function(data) {
                if (!data.actions.POST) {
                    $state.go("^");
                    Alert('Permission Error', 'You do not have permission to add an organization.', 'alert-info');
                }
            });

        ClearScope();

        var form = OrganizationForm(),
            base = $location.path().replace(/^\//, '').split('/')[0];

        init();

        function init(){
            // @issue What is this doing, why
            $scope.$emit("HideOrgListHeader");

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);
        }

        // Save
        $scope.formSave = function() {
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
                    $rootScope.$broadcast("EditIndicatorChange", "organizations", data.id);
                    $state.go('organizations.edit', {organization_id: data.id}, {reload: true});
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new organization. Post returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $scope.$emit("ShowOrgListHeader");
            $state.go('organizations');
        };
    }
];
