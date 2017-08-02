/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { N_ } from "../../i18n";

const user_type_options = [
 { type: 'normal', label: N_('Normal User') },
 { type: 'system_auditor', label: N_('System Auditor') },
 { type: 'system_administrator', label: N_('System Administrator') },
];

export default ['$scope', '$rootScope', '$stateParams', 'UserForm', 'Rest',
    'ProcessErrors', 'GetBasePath', 'Wait', 'CreateSelect2',
    '$state', 'i18n',
    function($scope, $rootScope, $stateParams, UserForm, Rest, ProcessErrors,
    GetBasePath, Wait, CreateSelect2, $state, i18n) {

        for (var i = 0; i < user_type_options.length; i++) {
            user_type_options[i].label = i18n._(user_type_options[i].label);
        }

        var form = UserForm,
            master = {},
            id = $stateParams.user_id,
            defaultUrl = GetBasePath('users') + id;

        init();

        function init() {
            $scope.hidePagination = false;
            $scope.hideSmartSearch = false;
            $scope.user_type_options = user_type_options;
            $scope.user_type = user_type_options[0];
            $scope.$watch('user_type', user_type_sync($scope));
            $scope.$watch('is_superuser', hidePermissionsTabSmartSearchAndPaginationIfSuperUser($scope));
            Rest.setUrl(defaultUrl);
            Wait('start');
            Rest.get(defaultUrl).success(function(data) {
                    $scope.user_id = id;
                    $scope.ldap_user = (data.ldap_dn !== null && data.ldap_dn !== undefined && data.ldap_dn !== '') ? true : false;
                    $scope.not_ldap_user = !$scope.ldap_user;
                    master.ldap_user = $scope.ldap_user;
                    $scope.socialAuthUser = (data.auth.length > 0) ? true : false;
                    $scope.external_account = data.external_account;

                    $scope.user_type = $scope.user_type_options[0];
                    $scope.is_system_auditor = false;
                    $scope.is_superuser = false;
                    if (data.is_system_auditor) {
                        $scope.user_type = $scope.user_type_options[1];
                        $scope.is_system_auditor = true;
                    }
                    if (data.is_superuser) {
                        $scope.user_type = $scope.user_type_options[2];
                        $scope.is_superuser = true;
                    }

                    $scope.user_obj = data;
                    $scope.name = data.username;

                    CreateSelect2({
                        element: '#user_user_type',
                        multiple: false
                    });

                    $scope.$watch('user_obj.summary_fields.user_capabilities.edit', function(val) {
                        if (val === false) {
                            $scope.canAdd = false;
                        }
                    });

                    setScopeFields(data);
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, {
                        hdr: i18n._('Error!'),
                        msg: i18n.sprintf(i18n._('Failed to retrieve user: %s. GET status: '), $stateParams.id) + status
                    });
                });
        }

        function user_type_sync($scope) {
            return (type_option) => {
                $scope.is_superuser = false;
                $scope.is_system_auditor = false;
                switch (type_option.type) {
                    case 'system_administrator':
                        $scope.is_superuser = true;
                        break;
                    case 'system_auditor':
                        $scope.is_system_auditor = true;
                        break;
                }
            };
        }

        // Organizations and Teams tab pagination is hidden through other mechanism
        function hidePermissionsTabSmartSearchAndPaginationIfSuperUser(scope) {
            return function(isSuperuserNewValue) {
                let shouldHide = isSuperuserNewValue;
                if (shouldHide === true) {
                    scope.hidePagination = true;
                    scope.hideSmartSearch = true;
                } else if (shouldHide === false) {
                    scope.hidePagination = false;
                    scope.hideSmartSearch = false;
                }
            };
        }


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

        $scope.redirectToResource = function(resource) {
            let type = resource.summary_fields.resource_type.replace(/ /g , "_");
            var id = resource.related[type].split("/")[4];
            switch (type) {
                case 'organization':
                    $state.go('organizations.edit', { "organization_id": id }, { reload: true });
                    break;
                case 'credential':
                    $state.go('credentials.edit', { "credential_id": id }, { reload: true });
                    break;
                case 'project':
                    $state.go('projects.edit', { "project_id": id }, { reload: true });
                    break;
                case 'inventory':
                    $state.go('inventories.edit', { "inventory_id": id }, { reload: true });
                    break;
                case 'job_template':
                    $state.go('templates.editJobTemplate', { "job_template_id": id }, { reload: true });
                    break;
                case 'workflow_job_template':
                    $state.go('templates.editWorkflowJobTemplate', { "workflow_job_template_id": id }, { reload: true });
                    break;
            }
        };

        // prepares a data payload for a PUT request to the API
        var processNewData = function(fields) {
            var data = {};
            _.forEach(fields, function(value, key) {
                if ($scope[key] !== '' && $scope[key] !== null && $scope[key] !== undefined) {
                    data[key] = $scope[key];
                }
            });
            data.is_superuser = $scope.is_superuser;
            data.is_system_auditor = $scope.is_system_auditor;
            return data;
        };

        $scope.formCancel = function() {
            $state.go('users', null, { reload: true });
        };

        $scope.formSave = function() {
            $rootScope.flashMessage = null;
            if ($scope[form.name + '_form'].$valid) {
                Rest.setUrl(defaultUrl + '/');
                var data = processNewData(form.fields);
                Rest.put(data).success(function() {
                        $state.go($state.current, null, { reload: true });
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: i18n._('Error!'),
                            msg: i18n.sprintf(i18n._('Failed to retrieve user: %s. GET status: '), $stateParams.id) + status
                        });
                    });
            }
        };

        $scope.clearPWConfirm = function(fld) {
            // If password value changes, make sure password_confirm must be re-entered
            $scope[fld] = '';
            $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
            $rootScope.flashMessage = null;
        };
    }
];
