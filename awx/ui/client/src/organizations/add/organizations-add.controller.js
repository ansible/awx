/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams', 'OrganizationForm', 
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'GetBasePath', 'Wait', 'CreateSelect2', 
    '$state','InstanceGroupsService', 'ConfigData', 'MultiCredentialService', 'defaultGalaxyCredential',
    function($scope, $rootScope, $location, $stateParams, OrganizationForm, 
        GenerateForm, Rest, Alert, ProcessErrors, GetBasePath, Wait, CreateSelect2, 
        $state, InstanceGroupsService, ConfigData, MultiCredentialService, defaultGalaxyCredential) {

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
            const virtualEnvs = ConfigData.custom_virtualenvs || [];
            $scope.custom_virtualenvs_visible = virtualEnvs.length > 1;
            $scope.custom_virtualenvs_options = virtualEnvs.filter(
                v => !/\/ansible\/$/.test(v)
            );
            CreateSelect2({
                element: '#organization_custom_virtualenv',
                multiple: false,
                opts: $scope.custom_virtualenvs_options
            });

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            $scope.credentials = defaultGalaxyCredential || [];
        }

        // Save
        $scope.formSave = function() {
            var fld, params = {};
            Wait('start');
            for (fld in form.fields) {
                params[fld] = $scope[fld];
            }
            if (!params.max_hosts || params.max_hosts === '') {
                params.max_hosts = 0;
            }
            var url = GetBasePath(base);
            url += (base !== 'organizations') ? $stateParams.project_id + '/organizations/' : '';
            Rest.setUrl(url);
            Rest.post(params)
                .then(({data}) => {
                    const organization_id = data.id,
                        instance_group_url = data.related.instance_groups;

                    MultiCredentialService
                        .saveRelatedSequentially({
                            related: {
                                credentials: data.related.galaxy_credentials
                            }
                        }, $scope.credentials)
                        .then(() => {
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
                        }).catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to save Galaxy credentials. POST returned status: ' + status
                            });
                        });

                })
                .catch(({data, status}) => {
                    let explanation = _.has(data, "name") ? data.name[0] : "";
                    ProcessErrors($scope, data, status, OrganizationForm, {
                        hdr: 'Error!',
                        msg: `Failed to save organization. POST status: ${status}. ${explanation}`
                    });
                });
        };

        $scope.formCancel = function() {
            $scope.$emit("ShowOrgListHeader");
            $state.go('organizations');
        };
    }
];
