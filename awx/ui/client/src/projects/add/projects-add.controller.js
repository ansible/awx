/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$location', '$stateParams', 'GenerateForm',
    'ProjectsForm', 'Rest', 'Alert', 'ProcessErrors', 'GetBasePath',
    'GetProjectPath', 'GetChoices', 'Wait', '$state', 'CreateSelect2', 'i18n',
    'ConfigData', 'resolvedModels', 'scmCredentialType', 'insightsCredentialType',
    function($scope, $location, $stateParams, GenerateForm, ProjectsForm, Rest,
    Alert, ProcessErrors, GetBasePath, GetProjectPath, GetChoices, Wait, $state,
    CreateSelect2, i18n, ConfigData, resolvedModels, scmCredentialType, insightsCredentialType) {

        let form = ProjectsForm(),
            base = $location.path().replace(/^\//, '').split('/')[0],
            defaultUrl = GetBasePath('projects'),
            main = {};

        init();

        function init() {
            $scope.canEditOrg = true;
            const virtualEnvs = ConfigData.custom_virtualenvs || [];
            $scope.custom_virtualenvs_options = virtualEnvs;

            const [ProjectModel] = resolvedModels;
            $scope.canAdd = ProjectModel.options('actions.POST');

            Rest.setUrl(GetBasePath('projects'));
            Rest.options()
            .then(({data}) => {
                if (!data.actions.POST) {
                    $state.go("^");
                    Alert(i18n._('Permission Error'), i18n._('You do not have permission to add a project.'), 'alert-info');
                }
            });

            CreateSelect2({
                element: '#project_custom_virtualenv',
                multiple: false,
                opts: $scope.custom_virtualenvs_options
            });

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);
        }

        GetProjectPath({ scope: $scope, main: main });

        if ($scope.removeChoicesReady) {
            $scope.removeChoicesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
            var i;
            for (i = 0; i < $scope.scm_type_options.length; i++) {
                if ($scope.scm_type_options[i].value === '') {
                    $scope.scm_type_options[i].value = "manual";
                    //$scope.scm_type = $scope.scm_type_options[i];
                    break;
                }
            }

            CreateSelect2({
                element: '#project_scm_type',
                multiple: false
            });

            $scope.scmRequired = false;
            main.scm_type = $scope.scm_type;
        });

        // Load the list of options for Kind
        GetChoices({
            scope: $scope,
            url: defaultUrl,
            field: 'scm_type',
            variable: 'scm_type_options',
            callback: 'choicesReady'
        });
        CreateSelect2({
            element: '#local-path-select',
            multiple: false
        });

        // Save
        $scope.formSave = function() {
            var i, fld, url, data = {};
            data = {};
            for (fld in form.fields) {
                if (form.fields[fld].type === 'checkbox_group') {
                    for (i = 0; i < form.fields[fld].fields.length; i++) {
                        data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                    }
                } else {
                    if (form.fields[fld].type !== 'alertblock') {
                        data[fld] = $scope[fld];
                    }
                }
            }

            if ($scope.scm_type.value === "manual") {
                data.scm_type = "";
                data.local_path = $scope.local_path.value;
            } else {
                data.scm_type = $scope.scm_type.value;
                delete data.local_path;
            }

            url = (base === 'teams') ? GetBasePath('teams') + $stateParams.team_id + '/projects/' : defaultUrl;
            Wait('start');
            Rest.setUrl(url);
            Rest.post(data)
                .then(({data}) => {
                    $scope.addedItem = data.id;
                    $state.go('projects.edit', { project_id: data.id }, { reload: true });
                })
                .catch(({data, status}) => {
                    Wait('stop');
                    ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'),
                        msg: i18n._('Failed to create new project. POST returned status: ') + status });
                });
        };

        $scope.scmChange = function() {
            // When an scm_type is set, path is not required
            if ($scope.scm_type) {
                $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
                $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
                $scope.scmBranchLabel = i18n._('SCM Branch');
                $scope.scmRefspecLabel = i18n._('SCM Refspec');
                // Dynamically update popover values
                if ($scope.scm_type.value) {
                    if(($scope.lookupType === 'insights_credential' && $scope.scm_type.value !== 'insights') || ($scope.lookupType === 'scm_credential' && $scope.scm_type.value === 'insights')) {
                        $scope.credential = null;
                        $scope.credential_name = '';
                    }
                    switch ($scope.scm_type.value) {
                        case 'git':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' +
                                i18n._('Example URLs for GIT SCM include:') +
                                '</p><ul class=\"no-bullets\"><li>https://github.com/ansible/ansible.git</li>' +
                                '<li>git@github.com:ansible/ansible.git</li><li>git://servername.example.com/ansible.git</li></ul>' +
                                '<p>' + i18n.sprintf(i18n._('%sNote:%s When using SSH protocol for GitHub or Bitbucket, enter an SSH key only, ' +
                                'do not enter a username (other than git). Additionally, GitHub and Bitbucket do not support password authentication when using ' +
                                'SSH. GIT read only protocol (git://) does not use username or password information.'), '<strong>', '</strong>');
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('SCM Branch/Tag/Commit');
                            break;
                        case 'svn':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Subversion SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://github.com/ansible/ansible</li><li>svn://servername.example.com/path</li>' +
                                '<li>svn+ssh://servername.example.com/path</li></ul>';
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('Revision #');
                            break;
                        case 'hg':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Mercurial SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://bitbucket.org/username/project</li><li>ssh://hg@bitbucket.org/username/project</li>' +
                                '<li>ssh://server.example.com/path</li></ul>' +
                                '<p>' + i18n.sprintf(i18n._('%sNote:%s Mercurial does not support password authentication for SSH. ' +
                                'Do not put the username and key in the URL. ' +
                                'If using Bitbucket and SSH, do not supply your Bitbucket username.'), '<strong>', '</strong>');
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('SCM Branch/Tag/Revision');
                            break;
                        case 'archive':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Remote Archive SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://github.com/username/project/archive/v0.0.1.tar.gz</li>' +
                                '<li>http://github.com/username/project/archive/v0.0.2.zip</li></ul>';
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            break;
                        case 'insights':
                            $scope.pathRequired = false;
                            $scope.scmRequired = false;
                            $scope.credRequired = true;
                            $scope.credentialLabel = "Credential";
                            $scope.lookupType = 'insights_credential';
                            break;
                        default:
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p> ' + i18n._('URL popover text') + '</p>';
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                    }
                }
            }
        };
        $scope.formCancel = function() {
            $state.go('projects');
        };
        $scope.lookupCredential = function(){
            // Perform a lookup on the credential_type. Git, Mercurial, and Subversion
            // all use SCM as their credential type.
            let lookupCredentialType = scmCredentialType;
            if ($scope.scm_type.value === 'insights') {
                lookupCredentialType = insightsCredentialType;
            }
            $state.go('.credential', {
                credential_search: {
                    credential_type: lookupCredentialType,
                    page_size: '5',
                    page: '1'
                }
            });
        };
    }
];
