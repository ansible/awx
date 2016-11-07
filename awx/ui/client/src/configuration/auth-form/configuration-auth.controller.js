/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$state',
    '$stateParams',
    '$timeout',
    '$q',
    'configurationGithubForm',
    'configurationGithubOrgForm',
    'configurationGithubTeamForm',
    'configurationGoogleForm',
    'configurationLdapForm',
    'configurationRadiusForm',
    'configurationSamlForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    'ParseTypeChange',
    'Wait',
    function(
        $scope,
        $state,
        $stateParams,
        $timeout,
        $q,
        configurationGithubForm,
        configurationGithubOrgForm,
        configurationGithubTeamForm,
        configurationGoogleForm,
        configurationLdapForm,
        configurationRadiusForm,
        configurationSamlForm,
        ConfigurationService,
        ConfigurationUtils,
        CreateSelect2,
        GenerateForm,
        ParseTypeChange,
        Wait
    ) {
        var authVm = this;

        var generator = GenerateForm;
        var formTracker = $scope.$parent.vm.formTracker;
        var dropdownValue = 'github';
        var activeAuthForm = 'github';

        // Default active form
        if ($stateParams.currentTab === '' || $stateParams.currentTab === 'auth') {
            formTracker.setCurrentAuth(activeAuthForm);
        }

        var activeForm = function() {
            if(!$scope.$parent[formTracker.currentFormName()].$dirty) {
                authVm.activeAuthForm = authVm.dropdownValue;
                formTracker.setCurrentAuth(authVm.activeAuthForm);
            } else {
                var msg = 'You have unsaved changes. Would you like to proceed <strong>without</strong> saving?';
                var title = 'Warning: Unsaved Changes';
                var buttons = [{
                    label: "Discard changes",
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $scope.$parent.vm.populateFromApi();
                        $scope.$parent[formTracker.currentFormName()].$setPristine();
                        authVm.activeAuthForm = authVm.dropdownValue;
                        formTracker.setCurrentAuth(authVm.activeAuthForm);
                        $('#FormModal-dialog').dialog('close');
                    }
                }, {
                    label: "Save changes",
                    onClick: function() {
                        $scope.$parent.vm.formSave()
                        .then(function() {
                            $scope.$parent[formTracker.currentFormName()].$setPristine();
                            $scope.$parent.vm.populateFromApi();
                            authVm.activeAuthForm = authVm.dropdownValue;
                            formTracker.setCurrentAuth(authVm.activeAuthForm);
                            $('#FormModal-dialog').dialog('close');
                        });
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                $scope.$parent.vm.triggerModal(msg, title, buttons);
            }
            formTracker.setCurrentAuth(authVm.activeAuthForm);
        };

        var dropdownOptions = [
            {label: 'Github', value: 'github'},
            {label: 'Github Org', value: 'github_org'},
            {label: 'Github Team', value: 'github_team'},
            {label: 'Google OAuth2', value: 'google_oauth'},
            {label: 'LDAP', value: 'ldap'},
            {label: 'RADIUS', value: 'radius'},
            {label: 'SAML', value: 'saml'}
        ];

        CreateSelect2({
            element: '#configure-dropdown-nav',
            multiple: false,
        });

        var authForms = [{
            formDef: configurationGithubForm,
            id: 'auth-github-form'
        }, {
            formDef: configurationGithubOrgForm,
            id: 'auth-github-org-form'
        }, {
            formDef: configurationGithubTeamForm,
            id: 'auth-github-team-form'
        }, {
            formDef: configurationGoogleForm,
            id: 'auth-google-form'
        }, {
            formDef: configurationLdapForm,
            id: 'auth-ldap-form'
        }, {
            formDef: configurationRadiusForm,
            id: 'auth-radius-form'
        }, {
            formDef: configurationSamlForm,
            id: 'auth-saml-form'
        }, ];

        var forms = _.pluck(authForms, 'formDef');

        _.each(forms, function(form) {
            var keys = _.keys(form.fields);
            _.each(keys, function(key) {
                if($scope.$parent.configDataResolve[key].type === 'choice') {
                    // Create options for dropdowns
                    var optionsGroup = key + '_options';
                    $scope.$parent[optionsGroup] = [];
                    _.each($scope.$parent.configDataResolve[key].choices, function(choice){
                        $scope.$parent[optionsGroup].push({
                            name: choice[0],
                            label: choice[1],
                            value: choice[0]
                        });
                    });
                }
                addFieldInfo(form, key);
            });
        });

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: ConfigurationUtils.formatPlaceholder($scope.$parent.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.$parent.configDataResolve[key].label
            });
        }

        $scope.$parent.parseType = 'json';

        _.each(authForms, function(form) {
            // Generate the forms
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent,
                related: true
            });
        });

        // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
        var dropdownRendered = false;

        $scope.$on('populated', function() {
            // Attach codemirror to fields that need it
            _.each(authForms, function(form) {
                    _.each(form.formDef.fields, function(field) {
                        // Codemirror balks at empty values so give it one
                        if($scope.$parent[field.name] === null && field.codeMirror) {
                          $scope.$parent[field.name] = '{}';
                        }
                        if(field.codeMirror) {
                            ParseTypeChange({
                               scope: $scope.$parent,
                               variable: field.name,
                               parse_variable: 'parseType',
                               field_id: form.formDef.name + '_' + field.name
                             });
                        }
                    });
            });

            // Create Select2 fields
            var opts = [];
            if($scope.$parent.AUTH_LDAP_GROUP_TYPE !== null) {
                opts.push({
                    id: $scope.$parent.AUTH_LDAP_GROUP_TYPE,
                    text: $scope.$parent.AUTH_LDAP_GROUP_TYPE
                });
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_ldap_template_AUTH_LDAP_GROUP_TYPE',
                    multiple: false,
                    placeholder: 'Select group types',
                    opts: opts
                });
                // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
                // TODO Find better solution for this bug
                $timeout(function(){
                    $scope.$parent.configuration_ldap_template_form.$setPristine();
                }, 1000);
            }

        });

        angular.extend(authVm, {
            activeForm: activeForm,
            activeAuthForm: activeAuthForm,
            authForms: authForms,
            dropdownOptions: dropdownOptions,
            dropdownValue: dropdownValue
        });
    }
];
