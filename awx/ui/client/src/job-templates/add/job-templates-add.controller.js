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

            ClearScope();

            // Inject dynamic view
            var defaultUrl = GetBasePath('job_templates'),
                form = JobTemplateForm(),
                generator = GenerateForm,
                master = {},
                CloudCredentialList = {},
                selectPlaybook, checkSCMStatus,
                callback,
                base = $location.path().replace(/^\//, '').split('/')[0],
                context = (base === 'job_templates') ? 'job_template' : 'inv';

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

            // Update playbook select whenever project value changes
            selectPlaybook = function (oldValue, newValue) {
                var url;
                if($scope.job_type.value === 'scan' && $scope.project_name === "Default"){
                    $scope.playbook_options = ['Default'];
                    $scope.playbook = 'Default';
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
                                Wait('stop');
                            })
                            .error(function (data, status) {
                                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                    msg: 'Failed to get playbook list for ' + url + '. GET returned status: ' + status });
                            });
                    }
                }
            };

            $scope.jobTypeChange = function(){
              if($scope.job_type){
                if($scope.job_type.value === 'scan'){
                    $scope.toggleScanInfo();
                  }
                  else if($scope.project_name === "Default"){
                    $scope.project_name = null;
                    $scope.playbook_options = [];
                    // $scope.playbook = 'null';
                    $scope.job_templates_form.playbook.$setPristine();
                  }
              }
            };

            $scope.toggleScanInfo = function() {
                $scope.project_name = 'Default';
                if($scope.project === null){
                  selectPlaybook();
                }
                else {
                  $scope.project = null;
                }
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
                            if (msg) {
                                Alert('Warning', msg, 'alert-info', null, null, null, null, true);
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
                                $scope.addedItem = data.id;

                                Refresh({
                                    scope: $scope,
                                    set: 'job_templates',
                                    iterator: 'job_template',
                                    url: $scope.current_url
                                });

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

                                saveCompleted();
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
                        } else {
                            if (fld !== 'variables' &&
                                fld !== 'survey') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }
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

                    Rest.setUrl(defaultUrl);
                    Rest.post(data)
                        .success(function(data) {
                            $scope.$emit('templateSaveSuccess',
                                data);
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
