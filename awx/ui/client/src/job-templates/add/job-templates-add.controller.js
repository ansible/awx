/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     [   'Refresh', '$filter', '$scope', '$rootScope', '$compile',
         '$location', '$log', '$stateParams', 'JobTemplateForm', 'GenerateForm',
         'Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 'ClearScope',
         'GetBasePath', 'InventoryList', 'CredentialList', 'ProjectList',
         'LookUpInit', 'md5Setup', 'ParseTypeChange', 'Wait', 'Empty', 'ToJSON',
         'CallbackHelpInit', 'initSurvey', 'Prompt', 'GetChoices', '$state',
         'CreateSelect2', '$q',
         function(
             Refresh, $filter, $scope, $rootScope, $compile,
             $location, $log, $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
             ProcessErrors, ReturnToCaller, ClearScope, GetBasePath, InventoryList,
             CredentialList, ProjectList, LookUpInit, md5Setup, ParseTypeChange, Wait,
             Empty, ToJSON, CallbackHelpInit, SurveyControllerInit, Prompt, GetChoices,
             $state, CreateSelect2, $q
         ) {

             Rest.setUrl(GetBasePath('job_templates'));
             Rest.options()
                 .success(function(data) {
                     if (!data.actions.POST) {
                         $state.go("^");
                         Alert('Permission Error', 'You do not have permission to add a job template.', 'alert-info');
                     }
                 });

            ClearScope();
            // Inject dynamic view
            var defaultUrl = GetBasePath('job_templates'),
                form = JobTemplateForm(),
                generator = GenerateForm,
                master = {},
                CloudCredentialList = {},
                NetworkCredentialList = {},
                selectPlaybook, checkSCMStatus,
                callback,
                base = $location.path().replace(/^\//, '').split('/')[0],
                context = (base === 'job_templates') ? 'job_template' : 'inv';

            // remove "type" field from search options
            CredentialList.fields.kind.noSearch = true;

            CallbackHelpInit({ scope: $scope });
            $scope.can_edit = true;
            generator.inject(form, { mode: 'add', related: false, scope: $scope });

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };
            $scope.mode = "add";
            $scope.parseType = 'yaml';
            ParseTypeChange({ scope: $scope, field_id: 'job_templates_variables', onChange: callback });

            $scope.playbook_options = [];
            $scope.allow_callbacks = false;

            generator.reset();

            md5Setup({
                scope: $scope,
                master: master,
                check_field: 'allow_callbacks',
                default_val: false
            });

            LookUpInit({
                scope: $scope,
                form: form,
                current_item: ($stateParams.inventory_id !== undefined) ? $stateParams.inventory_id : null,
                list: InventoryList,
                field: 'inventory',
                input_type: "radio"
            });


            // Clone the CredentialList object for use with cloud_credential. Cloning
            // and changing properties to avoid collision.
            jQuery.extend(true, CloudCredentialList, CredentialList);
            CloudCredentialList.name = 'cloudcredentials';
            CloudCredentialList.iterator = 'cloudcredential';
            CloudCredentialList.basePath = '/api/v1/credentials?cloud=true';

            // Clone the CredentialList object for use with network_credential. Cloning
            // and changing properties to avoid collision.
            jQuery.extend(true, NetworkCredentialList, CredentialList);
            NetworkCredentialList.name = 'networkcredentials';
            NetworkCredentialList.iterator = 'networkcredential';
            NetworkCredentialList.basePath = '/api/v1/credentials?kind=net';


            SurveyControllerInit({
                scope: $scope,
                parent_scope: $scope
            });

            if ($scope.removeLookUpInitialize) {
                $scope.removeLookUpInitialize();
            }
            $scope.removeLookUpInitialize = $scope.$on('lookUpInitialize', function () {
                LookUpInit({
                    url: GetBasePath('credentials') + '?cloud=true',
                    scope: $scope,
                    form: form,
                    current_item: null,
                    list: CloudCredentialList,
                    field: 'cloud_credential',
                    hdr: 'Select Cloud Credential',
                    input_type: 'radio'
                });

                LookUpInit({
                    url: GetBasePath('credentials') + '?kind=net',
                    scope: $scope,
                    form: form,
                    current_item: null,
                    list: NetworkCredentialList,
                    field: 'network_credential',
                    hdr: 'Select Network Credential',
                    input_type: 'radio'
                });

                LookUpInit({
                    url: GetBasePath('credentials') + '?kind=ssh',
                    scope: $scope,
                    form: form,
                    current_item: null,
                    list: CredentialList,
                    field: 'credential',
                    hdr: 'Select Machine Credential',
                    input_type: "radio"
                });
            });

            var selectCount = 0;

            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReadyVerbosity', function () {
                selectCount++;
                if (selectCount === 3) {
                    var verbosity;
                    // this sets the default options for the selects as specified by the controller.
                    for (verbosity in $scope.verbosity_options) {
                        if ($scope.verbosity_options[verbosity].isDefault) {
                            $scope.verbosity = $scope.verbosity_options[verbosity];
                        }
                    }
                    $scope.job_type = $scope.job_type_options[$scope.job_type_field.default];

                    // if you're getting to the form from the scan job section on inventories,
                    // set the job type select to be scan
                    if ($stateParams.inventory_id) {
                        // This means that the job template form was accessed via inventory prop's
                        // This also means the job is a scan job.
                        $scope.job_type.value = 'scan';
                        $scope.jobTypeChange();
                        $scope.inventory = $stateParams.inventory_id;
                        Rest.setUrl(GetBasePath('inventory') + $stateParams.inventory_id + '/');
                        Rest.get()
                            .success(function (data) {
                                $scope.inventory_name = data.name;
                            })
                            .error(function (data, status) {
                                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                    msg: 'Failed to lookup inventory: ' + data.id + '. GET returned status: ' + status });
                            });
                    }
                    CreateSelect2({
                        element:'#job_templates_job_type',
                        multiple: false
                    });
                    CreateSelect2({
                        element:'#job_templates_labels',
                        multiple: true,
                        addNew: true
                    });
                    CreateSelect2({
                        element:'#playbook-select',
                        multiple: false
                    });

                    CreateSelect2({
                        element:'#job_templates_verbosity',
                        multiple: false
                    });

                    $scope.$emit('lookUpInitialize');
                }
            });

            // setup verbosity options select
            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'verbosity',
                variable: 'verbosity_options',
                callback: 'choicesReadyVerbosity'
            });

            // setup job type options select
            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'job_type',
                variable: 'job_type_options',
                callback: 'choicesReadyVerbosity'
            });

            Rest.setUrl('api/v1/labels');
            Rest.get()
                .success(function (data) {
                    $scope.labelOptions = data.results
                        .map((i) => ({label: i.name, value: i.id}));
                    $scope.$emit("choicesReadyVerbosity");
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to get labels. GET returned ' +
                            'status: ' + status
                    });
                });

            function sync_playbook_select2() {
                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });
            }

            // Update playbook select whenever project value changes
            selectPlaybook = function (oldValue, newValue) {
                var url;
                if($scope.job_type.value === 'scan' && $scope.project_name === "Default"){
                    $scope.playbook_options = ['Default'];
                    $scope.playbook = 'Default';
                    sync_playbook_select2();
                    Wait('stop');
                }
                else if (oldValue !== newValue) {
                    if ($scope.project) {
                        Wait('start');
                        url = GetBasePath('projects') + $scope.project + '/playbooks/';
                        Rest.setUrl(url);
                        Rest.get()
                            .success(function (data) {
                                var i, opts = [];
                                for (i = 0; i < data.length; i++) {
                                    opts.push(data[i]);
                                }
                                $scope.playbook_options = opts;
                                sync_playbook_select2();
                                Wait('stop');
                            })
                            .error(function (data, status) {
                                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                    msg: 'Failed to get playbook list for ' + url + '. GET returned status: ' + status });
                            });
                    }
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

            $scope.resetProjectToDefault = function() {
                $scope.project_name = 'Default';
                $scope.project = null;
                selectPlaybook('force_load');
            };

            // Detect and alert user to potential SCM status issues
            checkSCMStatus = function (oldValue, newValue) {
                if (oldValue !== newValue && !Empty($scope.project)) {
                    Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
                    Rest.get()
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
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                msg: 'Failed to get project ' + $scope.project + '. GET returned status: ' + status });
                        });
                }
            };

            // Register a watcher on project_name
            if ($scope.selectPlaybookUnregister) {
                $scope.selectPlaybookUnregister();
            }
            $scope.selectPlaybookUnregister = $scope.$watch('project', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    selectPlaybook(oldValue, newValue);
                    checkSCMStatus();
                }
            });

            LookUpInit({
                scope: $scope,
                form: form,
                current_item: null,
                list: ProjectList,
                field: 'project',
                input_type: "radio",
                autopopulateLookup: (context === 'inv') ? false : true
            });

            if ($scope.removeSurveySaved) {
                $scope.rmoveSurveySaved();
            }
            $scope.removeSurveySaved = $scope.$on('SurveySaved', function() {
                Wait('stop');
                $scope.survey_exists = true;
                $scope.invalid_survey = false;
            });


            function saveCompleted(id) {
                $state.go('jobTemplates.edit', {id: id}, {reload: true});
            }

            if ($scope.removeTemplateSaveSuccess) {
                $scope.removeTemplateSaveSuccess();
            }
            $scope.removeTemplateSaveSuccess = $scope.$on('templateSaveSuccess', function(e, data) {
                Wait('stop');
                if (data.related &&
                    data.related.callback) {
                    Alert('Callback URL',
`<div>
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
</div>`,
                        'alert-danger', saveCompleted, null, null,
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
                    var labelsToAdd = ($scope.labels || [])
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
                                $scope.addedItem = data.id;

                                if($scope.survey_questions &&
                                    $scope.survey_questions.length > 0){
                                    //once the job template information
                                    // is saved we submit the survey
                                    // info to the correct endpoint
                                    var url = data.url+ 'survey_spec/';
                                    Rest.setUrl(url);
                                    Rest.post({ name: $scope.survey_name,
                                        description: $scope.survey_description,
                                        spec: $scope.survey_questions })
                                        .success(function () {
                                            Wait('stop');
                                        })
                                        .error(function (data,
                                            status) {
                                                ProcessErrors(
                                                    $scope,
                                                    data,
                                                    status,
                                                    form,
                                                    {
                                                        hdr: 'Error!',
                                                        msg: 'Failed to add new ' +
                                                        'survey. Post returned ' +
                                                        'status: ' +
                                                        status
                                                    });
                                        });
                                }

                                saveCompleted(data.id);
                            });
                    });
                });
            });

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
                    $("#job_templates_labels > option").filter("[data-select2-tag=true]").each(function(optionIndex, option) {
                        $("#job_templates_labels").siblings(".select2").first().find(".select2-selection__choice").each(function(labelIndex, label) {
                            if($(option).text() === $(label).attr('title')) {
                                // Mark that the option has a label present so that we can filter by that down below
                                $(option).attr('data-label-is-present', true);
                            }
                        });
                    });

                    $scope.newLabels = $("#job_templates_labels > option")
                        .filter("[data-select2-tag=true]")
                        .filter("[data-label-is-present=true]")
                        .map((i, val) => ({name: $(val).text()}));

                    Rest.setUrl(defaultUrl);
                    Rest.post(data)
                        .success(function(data) {
                            $scope.$emit('templateSaveSuccess',
                                data
                            );
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, form,
                                {
                                    hdr: 'Error!',
                                    msg: 'Failed to add new job ' +
                                    'template. POST returned status: ' +
                                    status
                                });
                        });

                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error parsing extra variables. " +
                        "Parser returned: " + err);
                }
            };

            $scope.formCancel = function () {
                $state.transitionTo('jobTemplates');
            };
        }
    ];
