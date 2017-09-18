/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     [   '$filter', '$scope',
        '$stateParams', 'JobTemplateForm', 'GenerateForm', 'Rest', 'Alert',
        'ProcessErrors', 'GetBasePath', 'md5Setup', 'ParseTypeChange', 'Wait',
        'Empty', 'ToJSON', 'CallbackHelpInit', 'GetChoices', '$state', 'availableLabels',
        'CreateSelect2', '$q', 'i18n', 'Inventory', 'Project', 'InstanceGroupsService', 'MultiCredentialService',
         function(
             $filter, $scope,
             $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
             ProcessErrors, GetBasePath, md5Setup, ParseTypeChange, Wait,
             Empty, ToJSON, CallbackHelpInit, GetChoices,
             $state, availableLabels, CreateSelect2, $q, i18n, Inventory, Project, InstanceGroupsService, MultiCredentialService
         ) {

            // Inject dynamic view
            let defaultUrl = GetBasePath('job_templates'),
                form = JobTemplateForm(),
                generator = GenerateForm,
                master = {},
                selectPlaybook, checkSCMStatus,
                callback;

            init();
            function init(){
                // apply form definition's default field values
                GenerateForm.applyDefaults(form, $scope);

                $scope.can_edit = true;
                $scope.allow_callbacks = false;
                $scope.playbook_options = [];
                $scope.mode = "add";
                $scope.parseType = 'yaml';
                $scope.credentialNotPresent = false;
                $scope.canGetAllRelatedResources = true;

                md5Setup({
                    scope: $scope,
                    master: master,
                    check_field: 'allow_callbacks',
                    default_val: false
                });
                CallbackHelpInit({ scope: $scope });

                $scope.surveyTooltip = i18n._('Please save before adding a survey to this job template.');
            }

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };

            var selectCount = 0;

            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReadyVerbosity', function () {
                ParseTypeChange({ scope: $scope, field_id: 'job_template_variables', onChange: callback });
                selectCount++;
                if (selectCount === 3) {
                    var verbosity;
                    // this sets the default options for the selects as specified by the controller.
                    for (verbosity in $scope.verbosity_options) {
                        if ($scope.verbosity_options[verbosity].isDefault) {
                            $scope.verbosity = $scope.verbosity_options[verbosity];
                        }
                    }
                    $scope.job_type = $scope.job_type_options[form.fields.job_type.default];

                    CreateSelect2({
                        element:'#job_template_job_type',
                        multiple: false
                    });
                    CreateSelect2({
                        element:'#job_template_labels',
                        multiple: true,
                        addNew: true
                    });
                    CreateSelect2({
                        element:'#playbook-select',
                        multiple: false
                    });
                    CreateSelect2({
                        element:'#job_template_verbosity',
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

            $scope.labelOptions = availableLabels
                .map((i) => ({label: i.name, value: i.id}));
            $scope.$emit("choicesReadyVerbosity");

            function sync_playbook_select2() {
                CreateSelect2({
                    element:'#playbook-select',
                    multiple: false
                });
            }

            $scope.toggleForm = function(key) {
                $scope[key] = !$scope[key];
            };

            // Update playbook select whenever project value changes
            selectPlaybook = function (oldValue, newValue) {
                var url;
                if (oldValue !== newValue) {
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

            $scope.jobTypeChange = function() {
                sync_playbook_select2();
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

            if(Inventory){
                $scope.inventory = Inventory.id;
                $scope.inventory_name = Inventory.name;
            }
            if(Project){
                $scope.project = Project.id;
                $scope.project_name = Project.name;
                selectPlaybook('force_load');
                checkSCMStatus();
            }

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

            if ($scope.removeSurveySaved) {
                $scope.removeSurveySaved();
            }
            $scope.removeSurveySaved = $scope.$on('SurveySaved', function() {
                Wait('stop');
                $scope.survey_exists = true;
                $scope.invalid_survey = false;
            });


            function saveCompleted(id) {
                $state.go('templates.editJobTemplate', {job_template_id: id}, {reload: true});
            }

            // Save
            $scope.formSave = function () {
                var fld, data = {};
                $scope.invalid_survey = false;

                // Can't have a survey enabled without a survey
                if($scope.survey_enabled === true &&
                    $scope.survey_exists !== true){
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
                            .machine) {
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

                    Rest.setUrl(defaultUrl);
                    Rest.post(data)
                        .then(({data}) => {

                            Wait('stop');
                            if (data.related && data.related.callback) {
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
                                    </p>`,
                                    'alert-danger', saveCompleted, null, null,
                                    null, true);
                            }

                            MultiCredentialService
                                .saveExtraCredentials({
                                    creds: $scope.selectedCredentials.extra,
                                    url: data.related.extra_credentials
                                });

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

                            const instance_group_url = data.related.instance_groups;
                            InstanceGroupsService.addInstanceGroups(instance_group_url, $scope.instance_groups)
                                .then(() => {
                                    Wait('stop');
                                })
                                .catch(({data, status}) => {
                                    ProcessErrors($scope, data, status, form, {
                                        hdr: 'Error!',
                                        msg: 'Failed to post instance groups. POST returned ' +
                                            'status: ' + status
                                    });
                                });
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to add new job ' +
                                'template. POST returned status: ' + status
                            });
                        });
                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error parsing extra variables. " +
                        "Parser returned: " + err);
                }
            };

            $scope.formCancel = function () {
                $state.transitionTo('templates');
            };
        }
    ];
