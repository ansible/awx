/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams',
    'OrganizationForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'GetBasePath', 'Wait', 'CreateSelect2', '$state','InstanceGroupsService', 'ConfigData',
    function($scope, $rootScope, $location, $stateParams, OrganizationForm,
    GenerateForm, Rest, Alert, ProcessErrors, GetBasePath, Wait, CreateSelect2, $state, InstanceGroupsService, ConfigData) {

        Rest.setUrl(GetBasePath('organizations'));
        Rest.options()
        .then(({data}) => {
            if (!data.actions.POST) {
                $state.go("^");
                Alert('Permission Error', 'You do not have permission to add an organization.', 'alert-info');
            }
        });

        var form = OrganizationForm(),
        base = $location.path().replace(/^\//, '').split('/')[0];
        init();

        function init(){
            // @issue What is this doing, why
            $scope.$emit("HideOrgListHeader");
            $scope.custom_virtualenvs_options = ConfigData.custom_virtualenvs;
            CreateSelect2({
                element: '#organization_custom_virtualenv',
                multiple: false,
                opts: $scope.custom_virtualenvs_options
            });

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
                    description: $scope.description,
                    custom_virtualenv: $scope.custom_virtualenv
                })
                .then(({data}) => {
                    const organization_id = data.id,
                        instance_group_url = data.related.instance_groups;

                    InstanceGroupsService.addInstanceGroups(instance_group_url, $scope.instance_groups)
                        .then(() => {
                            Wait('stop');
                            $rootScope.$broadcast("EditIndicatorChange", "organizations", organization_id);
                            $state.go('organizations.edit', {organization_id: organization_id}, {reload: true});
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to save instance groups. POST returned status: ' + status
                            });
                        });
                })
                .catch(({data, status}) => {
                    let explanation = _.has(data, "name") ? data.name[0] : "";
                    ProcessErrors($scope, data, status, OrganizationForm, {
                        hdr: 'Error!',
                        msg: `Failed to save organization. PUT status: ${status}. ${explanation}`
                    });
                });
        };

        $scope.formCancel = function() {
            $scope.$emit("ShowOrgListHeader");
            $state.go('organizations');
        };
    }
];
