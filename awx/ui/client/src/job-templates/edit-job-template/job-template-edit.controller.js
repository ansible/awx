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
    [   '$filter', '$scope', '$rootScope', '$compile',
        '$location', '$log', '$stateParams', 'JobTemplateForm', 'GenerateForm',
        'Rest', 'Alert',  'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'GetBasePath', 'md5Setup',
        'ParseTypeChange', 'JobStatusToolTip', 'FormatDate', 'Wait',
        'Empty', 'Prompt', 'ParseVariableString', 'ToJSON', 'GetChoices', 'CallbackHelpInit',
        'InitiatePlaybookRun' , 'initSurvey', '$state', 'CreateSelect2',
        'ToggleNotification','$q',
        function(
            $filter, $scope, $rootScope, $compile,
            $location, $log, $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
            ProcessErrors, ReturnToCaller, ClearScope, GetBasePath, md5Setup,
            ParseTypeChange, JobStatusToolTip, FormatDate, Wait,
            Empty, Prompt, ParseVariableString, ToJSON, GetChoices, CallbackHelpInit, InitiatePlaybookRun, SurveyControllerInit, $state,
            CreateSelect2, ToggleNotification, $q
        ) {

            ClearScope();

            $scope.$watch('job_template_obj.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAdd = false;
                }
            });

            var defaultUrl = GetBasePath('job_templates'),
                generator = GenerateForm,
                form = JobTemplateForm(),
                base = $location.path().replace(/^\//, '').split('/')[0],
                master = {},
                id = $stateParams.job_template_id,
                checkSCMStatus, getPlaybooks, callback,
                choicesCount = 0;

            init();
            function init(){
                CallbackHelpInit({ scope: $scope });
                $scope.playbook_options = null;
                $scope.playbook = null;
                $scope.mode = 'edit';
                $scope.parseType = 'yaml';
                $scope.showJobType = false;

                SurveyControllerInit({
                    scope: $scope,
                    parent_scope: $scope,
                    id: id
                });
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

            getPlaybooks = function (project) {
                var url;
                if ($scope.playbook) {
                    $scope.playbook_options = [$scope.playbook];
                }

                if($scope.job_type.value === 'scan' && $scope.project_name === "Default"){
                    $scope.playbook_options = ['Default'];
                    $scope.playbook = 'Default';
                    sync_playbook_select2();
                    Wait('stop');
                }
                else if (!Empty(project)) {
                    url = GetBasePath('projects') + project + '/playbooks/';
                    Wait('start');
                    Rest.setUrl(url);
                    Rest.get()
                        .success(function (data) {
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
                                $scope.$emit('jobTemplateLoadFinished');
                            } else {
                                Wait('stop');
                            }
                        })
                        .error(function (ret,status_code) {
                            if (status_code === 403) {
                                /* user doesn't have access to see the project, no big deal. */
                            } else {
                                Alert('Missing Playbooks', 'Unable to retrieve the list of playbooks for this project. Choose a different ' +
                                    ' project or make the playbooks available on the file system.', 'alert-info');
                            }
                            Wait('stop');
                        });
                }
                else {
                    Wait('stop');
                }
            };

            let last_non_scan_project_name = null;
            let last_non_scan_playbook = "";
            let last_non_scan_playbook_options = [];
            $scope.jobTypeChange = function() {
                if ($scope.job_type) {
                    if ($scope.job_type.value === 'scan') {
                        if ($scope.project_name !== "Default") {
                            last_non_scan_project_name = $scope.project_name;
                            last_non_scan_playbook = $scope.playbook;
                            last_non_scan_playbook_options = $scope.playbook_options;
                        }
                        // If the job_type is 'scan' then we don't want the user to be
                        // able to prompt for job type or inventory
                        $scope.ask_job_type_on_launch = false;
                        $scope.ask_inventory_on_launch = false;
                        $scope.resetProjectToDefault();
                    }
                    else if ($scope.project_name === "Default") {
                        $scope.project_name = last_non_scan_project_name;
                        $scope.playbook_options = last_non_scan_playbook_options;
                        $scope.playbook = last_non_scan_playbook;
                        $scope.job_template_form.playbook.$setPristine();
                    }
                }
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
                    url: defaultUrl,
                    id: id,
                    notifier: notifier,
                    column: column,
                    callback: 'NotificationRefresh'
                });
            };

            $scope.resetProjectToDefault = function() {
                $scope.project_name = 'Default';
                $scope.project = null;
                getPlaybooks();
            };

            // Detect and alert user to potential SCM status issues
            checkSCMStatus = function () {
                if (!Empty($scope.project)) {
                    Wait('start');
                    Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
                    Rest.get()
                        .success(function (data) {
                            console.log(data)
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
                            Wait('stop');
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
                        });
                }
            };

            // Register a watcher on project_name. Refresh the playbook list on change.
            if ($scope.watchProjectUnregister) {
                $scope.watchProjectUnregister();
            }
            $scope.watchProjectUnregister = $scope.$watch('project', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    getPlaybooks($scope.project);
                    checkSCMStatus();
                }
            });

            // watch for changes to 'verbosity', ensure we keep our select2 in sync when it changes.
            $scope.$watch('verbosity', sync_verbosity_select2);


            // Turn off 'Wait' after both cloud credential and playbook list come back
            if ($scope.removeJobTemplateLoadFinished) {
                $scope.removeJobTemplateLoadFinished();
            }
            $scope.removeJobTemplateLoadFinished = $scope.$on('jobTemplateLoadFinished', function () {
                CreateSelect2({
                    element:'#job_template_job_type',
                    multiple: false
                });

                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });

            });

            if ($scope.cloudCredentialReadyRemove) {
                $scope.cloudCredentialReadyRemove();
            }
            $scope.cloudCredentialReadyRemove = $scope.$on('cloudCredentialReady', function (e, name) {
                $scope.$emit('jobTemplateLoadFinished');
            });


            // Retrieve each related set and populate the playbook list
            if ($scope.jobTemplateLoadedRemove) {
                $scope.jobTemplateLoadedRemove();
            }
            $scope.jobTemplateLoadedRemove = $scope.$on('jobTemplateLoaded', function (e, related_cloud_credential, masterObject, relatedSets) {
                var dft;

                master = masterObject;
                getPlaybooks($scope.project);

                dft = ($scope.host_config_key === "" || $scope.host_config_key === null) ? false : true;
                md5Setup({
                    scope: $scope,
                    master: master,
                    check_field: 'allow_callbacks',
                    default_val: dft
                });

                ParseTypeChange({ scope: $scope, field_id: 'job_template_variables', onChange: callback });

                if($scope.job_template_obj.summary_fields.cloud_credential && related_cloud_credential) {
                    $scope.$emit('cloudCredentialReady', $scope.job_template_obj.summary_fields.cloud_credential.name);
                } else {
                    // No existing cloud credential
                    $scope.$emit('cloudCredentialReady', null);
                }

            });

            Wait('start');

            if ($scope.removeSurveySaved) {
                $scope.rmoveSurveySaved();
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
                $scope.fillJobTemplate();
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

            Rest.setUrl('api/v1/labels');
            Wait("start");
            Rest.get()
                .success(function (data) {
                    $scope.labelOptions = data.results
                        .map((i) => ({label: i.name, value: i.id}));

                    var seeMoreResolve = $q.defer();

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
                    if($state.params.job_template_id !== "null"){
                        Rest.setUrl(defaultUrl + $state.params.job_template_id +
                             "/labels");
                        Rest.get()
                            .success(function(data) {
                                if (data.next) {
                                    getNext(data, data.results, seeMoreResolve);
                                } else {
                                    seeMoreResolve.resolve(data.results);
                                }

                                seeMoreResolve.promise.then(function (labels) {
                                    $scope.$emit("choicesReady");
                                    var opts = labels
                                        .map(i => ({id: i.id + "",
                                            test: i.name}));
                                    CreateSelect2({
                                        element:'#job_template_labels',
                                        multiple: true,
                                        addNew: true,
                                        opts: opts
                                    });
                                    Wait("stop");
                                });
                            }).error(function(){
                                // job template id is null in this case
                                $scope.$emit("choicesReady");
                            });
                    }
                    else {
                        // job template doesn't exist
                        $scope.$emit("choicesReady");
                    }

                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to get labels. GET returned ' +
                            'status: ' + status
                    });
                });

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
`
<div>
    <p>Host callbacks are enabled for this template. The callback URL is:</p>
    <p style=\"padding: 10px 0;\">
        <strong>
            ${$scope.callback_server_path}
            ${data.related.callback}
        </string>
    </p>
    <p>The host configuration key is:
        <strong>
            ${$filter('sanitize')(data.host_config_key)}
        </string>
    </p>
</div>
`,
                        'alert-info', saveCompleted, null, null,
                        null, true);
                }
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

                // users can't save a survey with a scan job
                if($scope.job_type.value === "scan" &&
                    $scope.survey_enabled === true){
                    $scope.survey_enabled = false;
                }
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
                            fld !== 'playbook') {
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
                                fld !== 'survey') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }

                    data.ask_tags_on_launch = $scope.ask_tags_on_launch ? $scope.ask_tags_on_launch : false;
                    data.ask_skip_tags_on_launch = $scope.ask_skip_tags_on_launch ? $scope.ask_skip_tags_on_launch : false;
                    data.ask_limit_on_launch = $scope.ask_limit_on_launch ? $scope.ask_limit_on_launch : false;
                    data.ask_job_type_on_launch = $scope.ask_job_type_on_launch ? $scope.ask_job_type_on_launch : false;
                    data.ask_inventory_on_launch = $scope.ask_inventory_on_launch ? $scope.ask_inventory_on_launch : false;
                    data.ask_variables_on_launch = $scope.ask_variables_on_launch ? $scope.ask_variables_on_launch : false;
                    data.ask_credential_on_launch = $scope.ask_credential_on_launch ? $scope.ask_credential_on_launch : false;

                    data.extra_vars = ToJSON($scope.parseType,
                        $scope.variables, true);
                    if(data.job_type === 'scan' &&
                        $scope.default_scan === true){
                        data.project = "";
                        data.playbook = "";
                    }
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
                    Alert("Error", "Error parsing extra variables. " +
                        "Parser returned: " + err);
                }
            };

            $scope.formCancel = function () {
                $state.go('jobTemplates');
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
                        id: id
                    });
                }
            };
        }
    ];
