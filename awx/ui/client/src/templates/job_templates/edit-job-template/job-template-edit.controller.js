/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:JobTemplatesEdit
 * @description This controller's for Job Template Edit
*/

export default
    [   '$filter', '$scope', '$rootScope',
        '$location', '$stateParams', 'JobTemplateForm', 'GenerateForm',
        'Rest', 'Alert',  'ProcessErrors', 'GetBasePath', 'md5Setup',
        'ParseTypeChange', 'Wait', 'selectedLabels', 'i18n',
        'Empty', 'Prompt', 'ToJSON', 'GetChoices', 'CallbackHelpInit',
        'InitiatePlaybookRun' , 'initSurvey', '$state', 'CreateSelect2',
        'ToggleNotification','$q', 'InstanceGroupsService', 'InstanceGroupsData', 'MultiCredentialService', 'availableLabels',
        'projectGetPermissionDenied', 'inventoryGetPermissionDenied', 'jobTemplateData', 'ParseVariableString',
        function(
            $filter, $scope, $rootScope,
            $location, $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
            ProcessErrors, GetBasePath, md5Setup,
            ParseTypeChange, Wait, selectedLabels, i18n,
            Empty, Prompt, ToJSON, GetChoices, CallbackHelpInit, InitiatePlaybookRun, SurveyControllerInit, $state,
            CreateSelect2, ToggleNotification, $q, InstanceGroupsService, InstanceGroupsData, MultiCredentialService, availableLabels,
            projectGetPermissionDenied, inventoryGetPermissionDenied, jobTemplateData, ParseVariableString
        ) {

            $scope.$watch('job_template_obj.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAddJobTemplate = false;
                }
            });

            let defaultUrl = GetBasePath('job_templates'),
                generator = GenerateForm,
                form = JobTemplateForm(),
                base = $location.path().replace(/^\//, '').split('/')[0],
                master = {},
                id = $stateParams.job_template_id,
                callback,
                choicesCount = 0,
                instance_group_url = defaultUrl + id + '/instance_groups';

            init();
            function init() {

                CallbackHelpInit({ scope: $scope });

                $scope.playbook_options = null;
                $scope.playbook = null;
                $scope.mode = 'edit';
                $scope.parseType = 'yaml';
                $scope.showJobType = false;
                $scope.instance_groups = InstanceGroupsData;
                $scope.credentialNotPresent = false;
                $scope.surveyTooltip = i18n._('Surveys allow users to be prompted at job launch with a series of questions related to the job. This allows for variables to be defined that affect the playbook run at time of launch.');
                $scope.job_tag_options = [];
                $scope.skip_tag_options = [];

                SurveyControllerInit({
                    scope: $scope,
                    parent_scope: $scope,
                    id: id,
                    templateType: 'job_template'
                });

                $scope.$watch('project', function (newValue, oldValue) {
                    if (newValue !== oldValue) {
                        var url;
                        if ($scope.playbook) {
                            $scope.playbook_options = [$scope.playbook];
                        }

                        if (!Empty($scope.project) && $scope.job_template_obj.summary_fields.user_capabilities.edit) {
                            let promises = [];
                            url = GetBasePath('projects') + $scope.project + '/playbooks/';
                            Wait('start');
                            Rest.setUrl(url);
                            promises.push(Rest.get()
                                .success(function (data) {
                                    $scope.disablePlaybookBecausePermissionDenied = false;
                                    $scope.playbook_options = [];
                                    var playbookNotFound = true;
                                    for (var i = 0; i < data.length; i++) {
                                        $scope.playbook_options.push(data[i]);
                                        if (data[i] === $scope.playbook) {
                                            $scope.job_template_form.playbook.$setValidity('required', true);
                                            playbookNotFound = false;
                                        }
                                    }
                                    $scope.playbookNotFound = playbookNotFound;
                                    sync_playbook_select2();
                                    if ($scope.playbook) {
                                        jobTemplateLoadFinished();
                                    }
                                })
                                .error(function (ret,status_code) {
                                    if (status_code === 403) {
                                        /* user doesn't have access to see the project, no big deal. */
                                        $scope.disablePlaybookBecausePermissionDenied = true;
                                    } else {
                                        Alert('Missing Playbooks', 'Unable to retrieve the list of playbooks for this project. Choose a different ' +
                                            ' project or make the playbooks available on the file system.', 'alert-info');
                                    }
                                    Wait('stop');
                                }));


                            Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
                            promises.push(Rest.get()
                                .success(function (data) {
                                    var msg;
                                    switch (data.status) {
                                    case 'failed':
                                        msg = "<div>The Project selected has a status of \"failed\". You must run a successful update before you can select a playbook. You will not be able to save this Job Template without a valid playbook.";
                                        break;
                                    case 'never updated':
                                        msg = "<div>The Project selected has a status of \"never updated\". You must run a successful update before you can select a playbook. You will not be able to save this Job Template without a valid playbook.";
                                        break;
                                    case 'missing':
                                        msg = '<div>The selected project has a status of \"missing\". Please check the server and make sure ' +
                                            ' the directory exists and file permissions are set correctly.</div>';
                                        break;
                                    }
                                    if (msg) {
                                        Alert('Warning', msg, 'alert-info alert-info--noTextTransform', null, null, null, null, true);
                                    }
                                })
                                .error(function (data, status) {
                                    if (status === 403) {
                                        /* User doesn't have read access to the project, no problem. */
                                    } else {
                                        ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to get project ' + $scope.project +
                                            '. GET returned status: ' + status });
                                    }
                                }));

                            $q.all(promises)
                                .then(function(){
                                    Wait('stop');
                                });
                        }
                    }
                });

                // watch for changes to 'verbosity', ensure we keep our select2 in sync when it changes.
                $scope.$watch('verbosity', sync_verbosity_select2);
            }

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };

            function sync_playbook_select2() {
                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });
            }

            function sync_verbosity_select2() {
                CreateSelect2({
                    element:'#job_template_verbosity',
                    multiple: false
                });
            }

            function jobTemplateLoadFinished(){
                CreateSelect2({
                    element:'#job_template_job_type',
                    multiple: false
                });

                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });

                CreateSelect2({
                    element:'#job_template_job_tags',
                    multiple: true,
                    addNew: true
                });

                CreateSelect2({
                    element:'#job_template_skip_tags',
                    multiple: true,
                    addNew: true
                });
            }

            $scope.toggleForm = function(key) {
                $scope[key] = !$scope[key];
            };

            $scope.jobTypeChange = function() {
                sync_playbook_select2();
            };

            $scope.toggleNotification = function(event, notifier_id, column) {
                var notifier = this.notification;
                try {
                    $(event.target).tooltip('hide');
                }
                catch(e) {
                    // ignore
                }
                ToggleNotification({
                    scope: $scope,
                    url: defaultUrl + id,
                    notifier: notifier,
                    column: column,
                    callback: 'NotificationRefresh'
                });
            };

            // Retrieve each related set and populate the playbook list
            if ($scope.jobTemplateLoadedRemove) {
                $scope.jobTemplateLoadedRemove();
            }
            $scope.jobTemplateLoadedRemove = $scope.$on('jobTemplateLoaded', function (e, masterObject) {
                var dft;

                master = masterObject;

                dft = ($scope.host_config_key === "" || $scope.host_config_key === null) ? false : true;
                md5Setup({
                    scope: $scope,
                    master: master,
                    check_field: 'allow_callbacks',
                    default_val: dft
                });

                ParseTypeChange({ scope: $scope, field_id: 'job_template_variables', onChange: callback });

                jobTemplateLoadFinished();
            });

            Wait('start');

            if ($scope.removeSurveySaved) {
                $scope.removeSurveySaved();
            }
            $scope.removeSurveySaved = $scope.$on('SurveySaved', function() {
                Wait('stop');
                $scope.survey_exists = true;
                $scope.invalid_survey = false;
            });

            if ($scope.removeLoadJobs) {
                $scope.rmoveLoadJobs();
            }
            $scope.removeLoadJobs = $scope.$on('LoadJobs', function() {
                $scope.job_template_obj = jobTemplateData;
                $scope.name = jobTemplateData.name;
                var fld, i;
                for (fld in form.fields) {
                    if (fld !== 'variables' && fld !== 'survey' && fld !== 'forks' && jobTemplateData[fld] !== null && jobTemplateData[fld] !== undefined) {
                        if (form.fields[fld].type === 'select') {
                            if ($scope[fld + '_options'] && $scope[fld + '_options'].length > 0) {
                                for (i = 0; i < $scope[fld + '_options'].length; i++) {
                                    if (jobTemplateData[fld] === $scope[fld + '_options'][i].value) {
                                        $scope[fld] = $scope[fld + '_options'][i];
                                    }
                                }
                            } else {
                                $scope[fld] = jobTemplateData[fld];
                            }
                        } else {
                            $scope[fld] = jobTemplateData[fld];
                            if(!Empty(jobTemplateData.summary_fields.survey)) {
                                $scope.survey_exists = true;
                            }
                        }
                        master[fld] = $scope[fld];
                    }
                    if (fld === 'forks') {
                        if (jobTemplateData[fld] !== 0) {
                            $scope[fld] = jobTemplateData[fld];
                            master[fld] = $scope[fld];
                        }
                    }
                    if (fld === 'variables') {
                        // Parse extra_vars, converting to YAML.
                        $scope.variables = ParseVariableString(jobTemplateData.extra_vars);
                        master.variables = $scope.variables;
                    }
                    if (form.fields[fld].type === 'lookup' && jobTemplateData.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            jobTemplateData.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                    }
                    if (form.fields[fld].type === 'checkbox_group') {
                        for(var j=0; j<form.fields[fld].fields.length; j++) {
                            $scope[form.fields[fld].fields[j].name] = jobTemplateData[form.fields[fld].fields[j].name];
                        }
                    }
                }
                Wait('stop');
                $scope.url = jobTemplateData.url;

                $scope.survey_enabled = jobTemplateData.survey_enabled;

                $scope.ask_variables_on_launch = (jobTemplateData.ask_variables_on_launch) ? true : false;
                master.ask_variables_on_launch = $scope.ask_variables_on_launch;

                $scope.ask_verbosity_on_launch = (jobTemplateData.ask_verbosity_on_launch) ? true : false;
                master.ask_verbosity_on_launch = $scope.ask_verbosity_on_launch;

                $scope.ask_limit_on_launch = (jobTemplateData.ask_limit_on_launch) ? true : false;
                master.ask_limit_on_launch = $scope.ask_limit_on_launch;

                $scope.ask_tags_on_launch = (jobTemplateData.ask_tags_on_launch) ? true : false;
                master.ask_tags_on_launch = $scope.ask_tags_on_launch;

                $scope.ask_skip_tags_on_launch = (jobTemplateData.ask_skip_tags_on_launch) ? true : false;
                master.ask_skip_tags_on_launch = $scope.ask_skip_tags_on_launch;

                $scope.ask_diff_mode_on_launch = (jobTemplateData.ask_diff_mode_on_launch) ? true : false;
                master.ask_diff_mode_on_launch = $scope.ask_diff_mode_on_launch;

                $scope.job_tag_options = (jobTemplateData.job_tags) ? jobTemplateData.job_tags.split(',')
                    .map((i) => ({name: i, label: i, value: i})) : [];
                $scope.job_tags = $scope.job_tag_options;
                master.job_tags = $scope.job_tags;

                $scope.skip_tag_options = (jobTemplateData.skip_tags) ? jobTemplateData.skip_tags.split(',')
                    .map((i) => ({name: i, label: i, value: i})) : [];
                $scope.skip_tags = $scope.skip_tag_options;
                master.skip_tags = $scope.skip_tags;

                $scope.ask_job_type_on_launch = (jobTemplateData.ask_job_type_on_launch) ? true : false;
                master.ask_job_type_on_launch = $scope.ask_job_type_on_launch;

                $scope.ask_inventory_on_launch = (jobTemplateData.ask_inventory_on_launch) ? true : false;
                master.ask_inventory_on_launch = $scope.ask_inventory_on_launch;

                $scope.ask_credential_on_launch = (jobTemplateData.ask_credential_on_launch) ? true : false;
                master.ask_credential_on_launch = $scope.ask_credential_on_launch;

                if (jobTemplateData.host_config_key) {
                    $scope.example_config_key = jobTemplateData.host_config_key;
                }
                $scope.example_template_id = id;
                $scope.setCallbackHelp();

                $scope.callback_url = $scope.callback_server_path + ((jobTemplateData.related.callback) ? jobTemplateData.related.callback :
                GetBasePath('job_templates') + id + '/callback/');
                master.callback_url = $scope.callback_url;

                $scope.can_edit = jobTemplateData.summary_fields.user_capabilities.edit;

                if($scope.job_template_obj.summary_fields.user_capabilities.edit) {
                    MultiCredentialService.loadCredentials(jobTemplateData)
                        .then(([selectedCredentials, credTypes, credTypeOptions,
                            credTags, credentialGetPermissionDenied]) => {
                                $scope.canGetAllRelatedResources = !projectGetPermissionDenied && !inventoryGetPermissionDenied && !credentialGetPermissionDenied ? true : false;
                                $scope.selectedCredentials = selectedCredentials;
                                $scope.credential_types = credTypes;
                                $scope.credentialTypeOptions = credTypeOptions;
                                $scope.credentialsToPost = credTags;
                                $scope.$emit('jobTemplateLoaded', master);
                            });
                }
                else {

                    if (jobTemplateData.summary_fields.credential) {
                        $scope.selectedCredentials.machine = jobTemplateData.summary_fields.credential;
                    }

                    if (jobTemplateData.summary_fields.vault_credential) {
                        $scope.selectedCredentials.vault = jobTemplateData.summary_fields.vault_credential;
                    }

                    if (jobTemplateData.summary_fields.extra_credentials) {
                        $scope.selectedCredentials.extra = jobTemplateData.summary_fields.extra_credentials;
                    }

                    MultiCredentialService.getCredentialTypes()
                        .then(({credential_types, credentialTypeOptions}) => {
                            let typesArray = Object.keys(credential_types).map(key => credential_types[key]);
                            let credTypeOptions = credentialTypeOptions;

                            let machineAndVaultCreds = [],
                                extraCreds = [];

                            if($scope.selectedCredentials.machine) {
                                machineAndVaultCreds.push($scope.selectedCredentials.machine);
                            }
                            if($scope.selectedCredentials.vault) {
                                machineAndVaultCreds.push($scope.selectedCredentials.vault);
                            }

                            machineAndVaultCreds.map(cred => ({
                                name: cred.name,
                                id: cred.id,
                                postType: cred.postType,
                                kind: typesArray
                                    .filter(type => {
                                        return cred.kind === type.kind || parseInt(cred.credential_type) === type.value;
                                    })[0].name + ":"
                            }));

                            if($scope.selectedCredentials.extra && $scope.selectedCredentials.extra.length > 0) {
                                extraCreds = extraCreds.concat($scope.selectedCredentials.extra).map(cred => ({
                                    name: cred.name,
                                    id: cred.id,
                                    postType: cred.postType,
                                    kind: credTypeOptions
                                        .filter(type => {
                                            return parseInt(cred.credential_type_id) === type.value;
                                        })[0].name + ":"
                                }));
                            }

                            $scope.credentialsToPost = machineAndVaultCreds.concat(extraCreds);

                            $scope.$emit('jobTemplateLoaded', master);
                        });

                }
            });

            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
                choicesCount++;
                if (choicesCount === 5) {
                    $scope.$emit('LoadJobs');
                }
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('unified_jobs'),
                field: 'status',
                variable: 'status_choices',
                callback: 'choicesReady'
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('unified_jobs'),
                field: 'type',
                variable: 'type_choices',
                callback: 'choicesReady'
            });

            // setup verbosity options lookup
            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'verbosity',
                variable: 'verbosity_options',
                callback: 'choicesReady'
            });
            sync_verbosity_select2();

            // setup job type options lookup
            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'job_type',
                variable: 'job_type_options',
                callback: 'choicesReady'
            });

            $scope.labelOptions = availableLabels
                .map((i) => ({label: i.name, value: i.id}));

            var opts = selectedLabels
                .map(i => ({id: i.id + "",
                    test: i.name}));

            CreateSelect2({
                element:'#job_template_labels',
                multiple: true,
                addNew: true,
                opts: opts
            });

            $scope.$emit("choicesReady");

            function saveCompleted() {
                $state.go($state.current, {}, {reload: true});
            }

            if ($scope.removeTemplateSaveSuccess) {
                $scope.removeTemplateSaveSuccess();
            }
            $scope.removeTemplateSaveSuccess = $scope.$on('templateSaveSuccess', function(e, data) {
                Wait('stop');
                if (data.related &&
                    data.related.callback) {
                    Alert('Callback URL',
`Host callbacks are enabled for this template. The callback URL is:
<p style=\"padding: 10px 0;\">
    <strong>
        ${$scope.callback_server_path}
        ${data.related.callback}
    </strong>
</p>
<p>The host configuration key is:
    <strong>
        ${$filter('sanitize')(data.host_config_key)}
    </strong>
</p>
`,
                        'alert-danger', saveCompleted, null, null,
                        null, true);
                }

                MultiCredentialService
                    .findChangedExtraCredentials({
                        creds: $scope.selectedCredentials.extra,
                        url: data.related.extra_credentials
                    });

                InstanceGroupsService.editInstanceGroups(instance_group_url, $scope.instance_groups)
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to update instance groups. POST returned status: ' + status
                        });
                    });


                var orgDefer = $q.defer();
                var associationDefer = $q.defer();
                var associatedLabelsDefer = $q.defer();

                var getNext = function(data, arr, resolve) {
                    Rest.setUrl(data.next);
                    Rest.get()
                        .success(function (data) {
                            if (data.next) {
                                getNext(data, arr.concat(data.results), resolve);
                            } else {
                                resolve.resolve(arr.concat(data.results));
                            }
                        });
                };

                Rest.setUrl(data.related.labels);

                Rest.get()
                    .success(function(data) {
                        if (data.next) {
                            getNext(data, data.results, associatedLabelsDefer);
                        } else {
                            associatedLabelsDefer.resolve(data.results);
                        }
                    });

                associatedLabelsDefer.promise.then(function (current) {
                    current = current.map(data => data.id);
                    var labelsToAdd = $scope.labels
                        .map(val => val.value);
                    var labelsToDisassociate = current
                        .filter(val => labelsToAdd
                            .indexOf(val) === -1)
                        .map(val => ({id: val, disassociate: true}));
                    var labelsToAssociate = labelsToAdd
                        .filter(val => current
                            .indexOf(val) === -1)
                        .map(val => ({id: val, associate: true}));
                    var pass = labelsToDisassociate
                        .concat(labelsToAssociate);
                    associationDefer.resolve(pass);
                });

                Rest.setUrl(GetBasePath("organizations"));
                Rest.get()
                    .success(function(data) {
                        orgDefer.resolve(data.results[0].id);
                    });

                orgDefer.promise.then(function(orgId) {
                    var toPost = [];
                    $scope.newLabels = $scope.newLabels
                        .map(function(i, val) {
                            val.organization = orgId;
                            return val;
                        });

                    $scope.newLabels.each(function(i, val) {
                        toPost.push(val);
                    });

                    associationDefer.promise.then(function(arr) {
                        toPost = toPost
                            .concat(arr);

                        Rest.setUrl(data.related.labels);

                        var defers = [];
                        for (var i = 0; i < toPost.length; i++) {
                            defers.push(Rest.post(toPost[i]));
                        }
                        $q.all(defers)
                            .then(function() {
                                saveCompleted();
                            });
                    });
                });
            });



            // Save changes to the parent
            // Save
            $scope.formSave = function () {
                var fld, data = {};
                $scope.invalid_survey = false;

                // Can't have a survey enabled without a survey
                if($scope.survey_enabled === true &&
                    $scope.survey_exists!==true){
                    $scope.survey_enabled = false;
                }

                generator.clearApiErrors($scope);

                Wait('start');

                try {
                    for (fld in form.fields) {
                        if (form.fields[fld].type === 'select' &&
                            fld !== 'playbook' && $scope[fld]) {
                            data[fld] = $scope[fld].value;
                        }
                        else if(form.fields[fld].type === 'checkbox_group') {
                            // Loop across the checkboxes
                            for(var i=0; i<form.fields[fld].fields.length; i++) {
                                data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                            }
                        }
                        else {
                            if (fld !== 'variables' &&
                                fld !== 'survey' &&
                                fld !== 'forks') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }

                    data.forks = $scope.forks || 0;
                    data.ask_diff_mode_on_launch = $scope.ask_diff_mode_on_launch ? $scope.ask_diff_mode_on_launch : false;
                    data.ask_tags_on_launch = $scope.ask_tags_on_launch ? $scope.ask_tags_on_launch : false;
                    data.ask_skip_tags_on_launch = $scope.ask_skip_tags_on_launch ? $scope.ask_skip_tags_on_launch : false;
                    data.ask_limit_on_launch = $scope.ask_limit_on_launch ? $scope.ask_limit_on_launch : false;
                    data.ask_job_type_on_launch = $scope.ask_job_type_on_launch ? $scope.ask_job_type_on_launch : false;
                    data.ask_verbosity_on_launch = $scope.ask_verbosity_on_launch ? $scope.ask_verbosity_on_launch : false;
                    data.ask_inventory_on_launch = $scope.ask_inventory_on_launch ? $scope.ask_inventory_on_launch : false;
                    data.ask_variables_on_launch = $scope.ask_variables_on_launch ? $scope.ask_variables_on_launch : false;
                    data.ask_credential_on_launch = $scope.ask_credential_on_launch ? $scope.ask_credential_on_launch : false;
                    data.job_tags = (Array.isArray($scope.job_tags)) ? $scope.job_tags.join() : "";
                    data.skip_tags = (Array.isArray($scope.skip_tags)) ? $scope.skip_tags.join() : "";
                    if ($scope.selectedCredentials && $scope.selectedCredentials
                        .machine && $scope.selectedCredentials
                            .machine.id) {
                                data.credential = $scope.selectedCredentials
                                    .machine.id;
                    } else {
                        data.credential = null;
                    }
                    if ($scope.selectedCredentials && $scope.selectedCredentials
                        .vault && $scope.selectedCredentials
                            .vault.id) {
                                data.vault_credential = $scope.selectedCredentials
                                    .vault.id;
                    } else {
                        data.vault_credential = null;
                    }
                    data.extra_vars = ToJSON($scope.parseType,
                        $scope.variables, true);

                    // We only want to set the survey_enabled flag to
                    // true for this job template if a survey exists
                    // and it's been enabled.  By default,
                    // survey_enabled is explicitly set to true but
                    // if no survey is created then we don't want
                    // it enabled.
                    data.survey_enabled = ($scope.survey_enabled &&
                        $scope.survey_exists) ? $scope.survey_enabled : false;

                    // The idea here is that we want to find the new option elements that also have a label that exists in the dom
                    $("#job_template_labels > option").filter("[data-select2-tag=true]").each(function(optionIndex, option) {
                        $("#job_template_labels").siblings(".select2").first().find(".select2-selection__choice").each(function(labelIndex, label) {
                            if($(option).text() === $(label).attr('title')) {
                                // Mark that the option has a label present so that we can filter by that down below
                                $(option).attr('data-label-is-present', true);
                            }
                        });
                    });

                    $scope.newLabels = $("#job_template_labels > option")
                        .filter("[data-select2-tag=true]")
                        .filter("[data-label-is-present=true]")
                        .map((i, val) => ({name: $(val).text()}));

                    $scope.job_tags = _.map($scope.job_tags, function(i){return i.value;});
                    $("#job_template_job_tags").siblings(".select2").first().find(".select2-selection__choice").each(function(optionIndex, option){
                        $scope.job_tags.push(option.title);
                    });

                    $scope.skip_tags = _.map($scope.skip_tags, function(i){return i.value;});
                    $("#job_template_skip_tags").siblings(".select2").first().find(".select2-selection__choice").each(function(optionIndex, option){
                        $scope.skip_tags.push(option.title);
                    });

                    data.job_tags = (Array.isArray($scope.job_tags)) ? _.uniq($scope.job_tags).join() : "";
                    data.skip_tags = (Array.isArray($scope.skip_tags)) ?  _.uniq($scope.skip_tags).join() : "";


                    Rest.setUrl(defaultUrl + $state.params.job_template_id);
                    Rest.put(data)
                        .success(function (data) {
                            $scope.$emit('templateSaveSuccess', data);
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                msg: 'Failed to update job template. PUT returned status: ' + status });
                        });
                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error saving job template. " +
                        "Error: " + err);
                }
            };

            $scope.formCancel = function () {
                $state.go('templates');
            };

            // Related set: Add button
            $scope.add = function (set) {
                $rootScope.flashMessage = null;
                $location.path('/' + base + '/' + $stateParams.job_template_id + '/' + set);
            };

            // Related set: Edit button
            $scope.edit = function (set, id) {
                $rootScope.flashMessage = null;
                $location.path('/' + set + '/' + id);
            };

            // Launch a job using the selected template
            $scope.launch = function() {

                if ($scope.removePromptForSurvey) {
                    $scope.removePromptForSurvey();
                }
                $scope.removePromptForSurvey = $scope.$on('PromptForSurvey', function() {
                    var action = function () {
                            // $scope.$emit("GatherFormFields");
                            Wait('start');
                            $('#prompt-modal').modal('hide');
                            $scope.addSurvey();

                        };
                    Prompt({
                        hdr: 'Incomplete Survey',
                        body: '<div class="Prompt-bodyQuery">Do you want to create a survey before proceeding?</div>',
                        action: action
                    });
                });
                if($scope.survey_enabled === true && $scope.survey_exists!==true){
                    $scope.$emit("PromptForSurvey");
                }
                else {

                    InitiatePlaybookRun({
                        scope: $scope,
                        id: id,
                        job_type: 'job_template'
                    });
                }
            };
        }
    ];
