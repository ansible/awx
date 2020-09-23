/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$location', '$stateParams', 'isOrgAdmin', 'isNotificationAdmin',
    'OrganizationForm', 'Rest', 'ProcessErrors', 'Prompt', 'i18n', 'isOrgAuditor',
    'GetBasePath', 'Wait', '$state', 'ToggleNotification', 'CreateSelect2', 'InstanceGroupsService',
    'InstanceGroupsData', 'ConfigData', 'GalaxyCredentialsData', 'MultiCredentialService',
    function($scope, $location, $stateParams, isOrgAdmin, isNotificationAdmin,
        OrganizationForm, Rest, ProcessErrors, Prompt, i18n, isOrgAuditor,
        GetBasePath, Wait, $state, ToggleNotification, CreateSelect2, InstanceGroupsService,
        InstanceGroupsData, ConfigData, GalaxyCredentialsData, MultiCredentialService) {

        let form = OrganizationForm(),
            defaultUrl = GetBasePath('organizations'),
            base = $location.path().replace(/^\//, '').split('/')[0],
            main = {},
            id = $stateParams.organization_id,
            instance_group_url = defaultUrl + id + '/instance_groups/';

        $scope.isOrgAuditor = isOrgAuditor;
        $scope.isOrgAdmin = isOrgAdmin;
        $scope.isNotificationAdmin = isNotificationAdmin;

        $scope.$watch('organization_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });

        $scope.instance_groups = InstanceGroupsData;
        $scope.credentials = GalaxyCredentialsData;
        const virtualEnvs = ConfigData.custom_virtualenvs || [];
        $scope.custom_virtualenvs_visible = virtualEnvs.length > 1;
        $scope.custom_virtualenvs_options = virtualEnvs.filter(
            v => !/\/ansible\/$/.test(v)
        );

        // Retrieve detail record and prepopulate the form
        Wait('start');
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
        .then(({data}) => {
            let fld;

            $scope.sufficientRoleForNotifToggle = 
                isNotificationAdmin && (
                    $scope.is_system_auditor || 
                    isOrgAuditor ||
                    isOrgAdmin
                );

            $scope.sufficientRoleForNotif =  isNotificationAdmin || isOrgAuditor || $scope.user_is_system_auditor;
            
            $scope.organization_name = data.name;
            for (fld in form.fields) {
                if (typeof data[fld] !== 'undefined') {
                    $scope[fld] = data[fld];
                    main[fld] = data[fld];
                }
            }

            CreateSelect2({
                element: '#organization_custom_virtualenv',
                multiple: false,
                opts: $scope.custom_virtualenvs_options
            });

            $scope.organization_obj = data;
            $scope.$emit('organizationLoaded');
            Wait('stop');
        });

        $scope.toggleNotification = function(event, id, column) {
            var notifier = this.notification;
            try {
                $(event.target).tooltip('hide');
            } catch (e) {
                // ignore
            }
            ToggleNotification({
                scope: $scope,
                url: defaultUrl,
                id: $scope.organization_id,
                notifier: notifier,
                column: column,
                callback: 'NotificationRefresh'
            });
        };

        // Save changes to the parent
        $scope.formSave = function() {
            var fld, params = {};
            Wait('start');
            for (fld in form.fields) {
                params[fld] = $scope[fld];
            }
            if (!params.max_hosts || params.max_hosts === '') {
                params.max_hosts = 0;
            }
            Rest.setUrl(defaultUrl + id + '/');
            Rest.put(params)
                .then(() => {
                    MultiCredentialService
                    .saveRelatedSequentially({
                        related: {
                            credentials: $scope.organization_obj.related.galaxy_credentials
                        }
                    }, $scope.credentials)
                    .then(() => {
                        InstanceGroupsService.editInstanceGroups(instance_group_url, $scope.instance_groups)
                        .then(() => {
                            Wait('stop');
                            $state.go($state.current, {}, { reload: true });
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to update instance groups. POST returned status: ' + status
                            });
                        });
                    }).catch(({data, status}) => {
                        ProcessErrors($scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to save Galaxy credentials. POST returned status: ' + status
                        });
                    });
                    $scope.organization_name = $scope.name;
                    main = params;
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, OrganizationForm, {
                        hdr: 'Error!',
                        msg: 'Failed to update organization: ' + id + '. PUT status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
            $scope.$emit("ShowOrgListHeader");
        };

        // Related set: Add button
        $scope.add = function(set) {
            $location.path('/' + base + '/' + $stateParams.organization_id + '/' + set);
        };

        // Related set: Edit button
        $scope.edit = function(set, id) {
            $location.path('/' + set + '/' + id);
        };

        // Related set: Delete button
        $scope['delete'] = function(set, itm_id, name, title) {

            var action = function() {
                Wait('start');
                var url = defaultUrl + $stateParams.organization_id + '/' + set + '/';
                Rest.setUrl(url);
                Rest.post({ id: itm_id, disassociate: 1 })
                    .then(() => {
                        $('#prompt-modal').modal('hide');
                    })
                    .catch(({data, status}) => {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. POST returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the ' + title + ' below from ' + $scope.name + '?</div><div class="Prompt-bodyTarget">' + name + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });

        };
    }
];
