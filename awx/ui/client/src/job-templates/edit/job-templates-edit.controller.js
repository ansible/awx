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
        'Rest', 'Alert',  'ProcessErrors', 'RelatedSearchInit',
        'RelatedPaginateInit','ReturnToCaller', 'ClearScope', 'InventoryList',
        'CredentialList', 'ProjectList', 'LookUpInit', 'GetBasePath', 'md5Setup',
        'ParseTypeChange', 'JobStatusToolTip', 'FormatDate', 'Wait',
        'Empty', 'Prompt', 'ParseVariableString', 'ToJSON',
        'SchedulesControllerInit', 'JobsControllerInit', 'JobsListUpdate',
        'GetChoices', 'SchedulesListInit', 'SchedulesList', 'CallbackHelpInit',
        'InitiatePlaybookRun' , 'initSurvey', '$state', 'CreateSelect2',
        'ToggleNotification', 'NotificationsListInit', '$q',
        function(
            $filter, $scope, $rootScope, $compile,
            $location, $log, $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
            ProcessErrors, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller,
            ClearScope, InventoryList, CredentialList, ProjectList, LookUpInit,
            GetBasePath, md5Setup, ParseTypeChange, JobStatusToolTip, FormatDate, Wait,
            Empty, Prompt, ParseVariableString, ToJSON, SchedulesControllerInit,
            JobsControllerInit, JobsListUpdate, GetChoices, SchedulesListInit,
            SchedulesList, CallbackHelpInit, InitiatePlaybookRun, SurveyControllerInit, $state,
            CreateSelect2, ToggleNotification, NotificationsListInit, $q
        ) {

            ClearScope();

            var defaultUrl = GetBasePath('job_templates'),
                generator = GenerateForm,
                form = JobTemplateForm(),
                base = $location.path().replace(/^\//, '').split('/')[0],
                master = {},
                id = $stateParams.template_id,
                relatedSets = {},
                checkSCMStatus, getPlaybooks, callback,
                choicesCount = 0;


            CallbackHelpInit({ scope: $scope });

            SchedulesList.well = false;
            generator.inject(form, { mode: 'edit', related: true, scope: $scope });
            $scope.mode = 'edit';
            $scope.parseType = 'yaml';
            $scope.showJobType = false;

            SurveyControllerInit({
                scope: $scope,
                parent_scope: $scope,
                id: id
            });

            NotificationsListInit({
                scope: $scope,
                url: GetBasePath('job_templates'),
                id: id
            });

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };

            $scope.playbook_options = null;
            $scope.playbook = null;
            generator.reset();

            function sync_playbook_select2() {
                CreateSelect2({
                    element:'#playbook-select',
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
                            for (var i = 0; i < data.length; i++) {
                                $scope.playbook_options.push(data[i]);
                                if (data[i] === $scope.playbook) {
                                    $scope.job_templates_form.playbook.$setValidity('required', true);
                                }
                            }
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
                        $scope.job_templates_form.playbook.$setPristine();
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
                            var msg;
                            switch (data.status) {
                            case 'failed':
                                msg = "The selected project has a <em>failed</em> status. Review the project's SCM settings" +
                                    " and run an update before adding it to a template.";
                                break;
                            case 'never updated':
                                msg = 'The selected project has a <em>never updated</em> status. You will need to run a successful' +
                                    ' update in order to selected a playbook. Without a valid playbook you will not be able ' +
                                    ' to save this template.';
                                break;
                            case 'missing':
                                msg = 'The selected project has a status of <em>missing</em>. Please check the server and make sure ' +
                                    ' the directory exists and file permissions are set correctly.';
                                break;
                            }
                            Wait('stop');
                            if (msg) {
                                Alert('Warning', msg, 'alert-info', null, null, null, null, true);
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

            if ($scope.removerelatedschedules) {
                $scope.removerelatedschedules();
            }
            $scope.removerelatedschedules = $scope.$on('relatedschedules', function() {
                SchedulesListInit({
                    scope: $scope,
                    list: SchedulesList,
                    choices: null,
                    related: true
                });
            });

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



            // Turn off 'Wait' after both cloud credential and playbook list come back
            if ($scope.removeJobTemplateLoadFinished) {
                $scope.removeJobTemplateLoadFinished();
            }
            $scope.removeJobTemplateLoadFinished = $scope.$on('jobTemplateLoadFinished', function () {
                CreateSelect2({
                    element:'#job_templates_job_type',
                    multiple: false
                });

                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });

                for (var set in relatedSets) {
                    $scope.search(relatedSets[set].iterator);
                }
                SchedulesControllerInit({
                    scope: $scope,
                    parent_scope: $scope,
                    iterator: 'schedule'
                });

            });

            // Set the status/badge for each related job
            if ($scope.removeRelatedCompletedJobs) {
                $scope.removeRelatedCompletedJobs();
            }
            $scope.removeRelatedCompletedJobs = $scope.$on('relatedcompleted_jobs', function () {
                JobsControllerInit({
                    scope: $scope,
                    parent_scope: $scope,
                    iterator: form.related.completed_jobs.iterator
                });
                JobsListUpdate({
                    scope: $scope,
                    parent_scope: $scope,
                    list: form.related.completed_jobs
                });
            });

            if ($scope.cloudCredentialReadyRemove) {
                $scope.cloudCredentialReadyRemove();
            }
            $scope.cloudCredentialReadyRemove = $scope.$on('cloudCredentialReady', function (e, name) {
                var CloudCredentialList = {};
                $scope.cloud_credential_name = name;
                master.cloud_credential_name = name;
                // Clone the CredentialList object for use with cloud_credential. Cloning
                // and changing properties to avoid collision.
                jQuery.extend(true, CloudCredentialList, CredentialList);
                CloudCredentialList.name = 'cloudcredentials';
                CloudCredentialList.iterator = 'cloudcredential';
                CloudCredentialList.basePath = '/api/v1/credentials?cloud=true';
                LookUpInit({
                    url: GetBasePath('credentials') + '?cloud=true',
                    scope: $scope,
                    form: form,
                    current_item: $scope.cloud_credential,
                    list: CloudCredentialList,
                    field: 'cloud_credential',
                    hdr: 'Select Cloud Credential',
                    input_type: "radio"
                });
                $scope.$emit('jobTemplateLoadFinished');
            });


            // Retrieve each related set and populate the playbook list
            if ($scope.jobTemplateLoadedRemove) {
                $scope.jobTemplateLoadedRemove();
            }
            $scope.jobTemplateLoadedRemove = $scope.$on('jobTemplateLoaded', function (e, related_cloud_credential, masterObject, relatedSets) {
                var dft, set;
                master = masterObject;
                getPlaybooks($scope.project);

                for (set in relatedSets) {
                    $scope.search(relatedSets[set].iterator);
                }

                dft = ($scope.host_config_key === "" || $scope.host_config_key === null) ? false : true;
                md5Setup({
                    scope: $scope,
                    master: master,
                    check_field: 'allow_callbacks',
                    default_val: dft
                });

                ParseTypeChange({ scope: $scope, field_id: 'job_templates_variables', onChange: callback });

                if (related_cloud_credential) {
                    Rest.setUrl(related_cloud_credential);
                    Rest.get()
                        .success(function (data) {
                            $scope.$emit('cloudCredentialReady', data.name);
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, null, {hdr: 'Error!',
                                msg: 'Failed to related cloud credential. GET returned status: ' + status });
                        });
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
                .success(function () {
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

                    Rest.setUrl(defaultUrl + $state.params.template_id +
                         "/labels");
                    Rest.get()
                        .success(function(data) {
                            if (data.next) {
                                getNext(data, data.results, seeMoreResolve);
                            } else {
                                seeMoreResolve.resolve(data.results);
                            }

                            seeMoreResolve.promise.then(function (labels) {
                                $scope.labelOptions = labels
                                    .map((i) => ({label: i.name, value: i.id}));
                                $scope.$emit("choicesReady");
                                var opts = labels
                                    .map(i => ({id: i.id + "",
                                        test: i.name}));
                                CreateSelect2({
                                    element:'#job_templates_labels',
                                    multiple: true,
                                    addNew: true,
                                    opts: opts
                                });
                                Wait("stop");
                            });
                        });

                    CreateSelect2({
                        element:'#job_templates_verbosity',
                        multiple: false
                    });
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to get labels. GET returned ' +
                            'status: ' + status
                    });
                });

            function saveCompleted() {
                $state.go('jobTemplates', null, {reload: true});
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
`,
                        'alert-info', saveCompleted, null, null,
                        null, true);
                }
                var orgDefer = $q.defer();
                var associationDefer = $q.defer();

                Rest.setUrl(data.related.labels);

                var currentLabels = Rest.get()
                    .then(function(data) {
                        return data.data.results
                            .map(val => val.id);
                    });

                currentLabels.then(function (current) {
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

                generator.clearApiErrors();

                Wait('start');

                try {
                    for (fld in form.fields) {
                        if (form.fields[fld].type === 'select' &&
                            fld !== 'playbook') {
                            data[fld] = $scope[fld].value;
                        } else {
                            if (fld !== 'variables' &&
                                fld !== 'survey') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }

                    data.ask_tags_on_launch = $scope.ask_tags_on_launch ? $scope.ask_tags_on_launch : false;
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

                    $scope.newLabels = $("#job_templates_labels > option")
                        .filter("[data-select2-tag=true]")
                        .map((i, val) => ({name: $(val).text()}));

                    Rest.setUrl(defaultUrl + $state.params.template_id);
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
                // the form was just copied in the previous state, it's safe to destroy on cancel
                if ($state.params.copied){
                    var defaultUrl = GetBasePath('job_templates') + $state.params.template_id;
                    Rest.setUrl(defaultUrl);
                    Rest.destroy()
                        .success(function(){
                            $state.go('jobTemplates', null, {reload: true, notify:true});
                        })
                        .error(function(res, status){
                            ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
                            msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
                        });
                }
                else {
                    $state.go('jobTemplates');
                }
            };

            // Related set: Add button
            $scope.add = function (set) {
                $rootScope.flashMessage = null;
                $location.path('/' + base + '/' + $stateParams.template_id + '/' + set);
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
