/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     [   '$filter', '$scope',
        '$stateParams', 'JobTemplateForm', 'GenerateForm', 'Rest', 'Alert',
        'ProcessErrors', 'GetBasePath', 'hashSetup', 'ParseTypeChange', 'Wait',
        'Empty', 'ToJSON', 'CallbackHelpInit', 'GetChoices', '$state', 'availableLabels',
        'CreateSelect2', '$q', 'i18n', 'Inventory', 'Project', 'InstanceGroupsService',
        'MultiCredentialService', 'ConfigData', 'resolvedModels', '$compile',
         function(
             $filter, $scope,
             $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
             ProcessErrors, GetBasePath, hashSetup, ParseTypeChange, Wait,
             Empty, ToJSON, CallbackHelpInit, GetChoices,
             $state, availableLabels, CreateSelect2, $q, i18n, Inventory, Project, InstanceGroupsService,
             MultiCredentialService, ConfigData, resolvedModels, $compile
         ) {

            // Inject dynamic view
            let defaultUrl = GetBasePath('job_templates'),
                form = JobTemplateForm(),
                generator = GenerateForm,
                main = {},
                selectPlaybook, checkSCMStatus,
                callback;

            const jobTemplate = resolvedModels[0];

            $scope.canAddJobTemplate = jobTemplate.options('actions.POST');
            $scope.disableLaunch = true;

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            $scope.can_edit = true;
            $scope.allow_callbacks = false;
            $scope.playbook_options = [];
            $scope.webhook_service_options = [];
            $scope.mode = "add";
            $scope.parseType = 'yaml';
            $scope.credentialNotPresent = false;
            $scope.canGetAllRelatedResources = true;
            $scope.webhook_key_help = i18n._('Webhook services can use this as a shared secret.');

            //
            // webhook credential - all handlers, dynamic state, etc. live here
            //

            $scope.webhookCredential = {
                id: null,
                name: null,
                isModalOpen: false,
                isModalReady: false,
                modalTitle: i18n._('Select Webhook Credential'),
                modalBaseParams: {
                    order_by: 'name',
                    page_size: 5,
                    credential_type__namespace: null,
                },
                modalSelectedId: null,
                modalSelectedName: null,
            };

            $scope.handleWebhookCredentialLookupClick = () => {
                $scope.webhookCredential.modalSelectedId = $scope.webhookCredential.id;
                $scope.webhookCredential.isModalOpen = true;
            };

            $scope.handleWebhookCredentialTagDelete = () => {
                $scope.webhookCredential.id = null;
                $scope.webhookCredential.name = null;
            };

            $scope.handleWebhookCredentialModalClose = () => {
                $scope.webhookCredential.isModalOpen = false;
                $scope.webhookCredential.isModalReady = false;
            };

            $scope.handleWebhookCredentialModalReady = () => {
                $scope.webhookCredential.isModalReady = true;
            };

            $scope.handleWebhookCredentialModalItemSelect = (item) => {
                $scope.webhookCredential.modalSelectedId = item.id;
                $scope.webhookCredential.modalSelectedName = item.name;
            };

            $scope.handleWebhookCredentialModalCancel = () => {
                $scope.webhookCredential.isModalOpen = false;
                $scope.webhookCredential.isModalReady = false;
                $scope.webhookCredential.modalSelectedId = null;
                $scope.webhookCredential.modalSelectedName = null;

            };

            $scope.handleWebhookCredentialSelect = () => {
                $scope.webhookCredential.isModalOpen = false;
                $scope.webhookCredential.isModalReady = false;
                $scope.webhookCredential.id = $scope.webhookCredential.modalSelectedId;
                $scope.webhookCredential.name = $scope.webhookCredential.modalSelectedName;
                $scope.webhookCredential.modalSelectedId = null;
                $scope.webhookCredential.modalSelectedName = null;
            };

            $scope.handleWebhookKeyButtonClick = () => {};

            $('#content-container').append($compile(`
                <at-dialog
                    title="webhookCredential.modalTitle"
                    on-close="handleWebhookCredentialModalClose"
                    ng-if="webhookCredential.isModalOpen"
                    ng-show="webhookCredential.isModalOpen && webhookCredential.isModalReady"
                >
                    <at-lookup-list
                        ng-show="webhookCredential.isModalOpen && webhookCredential.isModalReady"
                        resource-name="credential"
                        base-params="webhookCredential.modalBaseParams"
                        selected-id="webhookCredential.modalSelectedId"
                        on-ready="handleWebhookCredentialModalReady"
                        on-item-select="handleWebhookCredentialModalItemSelect"
                    ></at-lookup-list>
                    <at-action-group col="12" pos="right">
                        <at-action-button
                            variant="tertiary"
                            ng-click="handleWebhookCredentialModalCancel()"
                        >
                            ${i18n._('CANCEL')}
                        </at-action-button>
                        <at-action-button
                            variant="primary"
                            ng-click="handleWebhookCredentialSelect()"
                        >
                            ${i18n._('SELECT')}
                        </at-action-button>
                    </at-action-group>
                </at-dialog>`)($scope));

            $scope.$watch('webhook_service', (newValue, oldValue) => {
                const newServiceValue = newValue && typeof newValue === 'object' ? newValue.value : newValue;
                const oldServiceValue = oldValue && typeof oldValue === 'object' ? oldValue.value : oldValue;
                if (newServiceValue !== oldServiceValue || newServiceValue === newValue) {
                    $scope.webhook_service = { value: newServiceValue };
                    sync_webhook_service_select2();
                    $scope.webhookCredential.modalBaseParams.credential_type__namespace = newServiceValue ?
                        `${newServiceValue}_token`
                        : null;
                    if (newServiceValue !== newValue || newValue === null) {
                        $scope.webhookCredential.id = null;
                        $scope.webhookCredential.name = null;
                    }
                }
            });

            hashSetup({
                scope: $scope,
                main: main,
                check_field: 'allow_callbacks',
                default_val: false
            });
            CallbackHelpInit({ scope: $scope });
            // set initial vals for webhook checkbox
            $scope.enable_webhook = false;
            main.enable_webhook = false;

            $scope.surveyTooltip = i18n._('Please save before adding a survey to this job template.');

            MultiCredentialService.getCredentialTypes()
            .then(({ data }) => {
                $scope.multiCredential = {
                    credentialTypes: data.results,
                    selectedCredentials: []
                };
            });

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };

            var selectCount = 0;

            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReadyVerbosity', function () {
                ParseTypeChange({
                    scope: $scope,
                    field_id: 'extra_vars',
                    variable: 'extra_vars',
                    onChange: callback
                });

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
                    const virtualEnvs = ConfigData.custom_virtualenvs || [];
                    $scope.custom_virtualenvs_options = virtualEnvs;

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
                        addNew: true,
                        multiple: false,
                        scope: $scope,
                        options: 'playbook_options',
                        model: 'playbook'
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

                    CreateSelect2({
                        element: '#job_template_custom_virtualenv',
                        multiple: false,
                        opts: $scope.custom_virtualenvs_options
                    });
                    CreateSelect2({
                        element:'#webhook-service-select',
                        addNew: false,
                        multiple: false,
                        scope: $scope,
                        options: 'webhook_service_options',
                        model: 'webhook_service'
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
            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'webhook_service',
                variable: 'webhook_service_options',
                callback: 'choicesReadyVerbosity'
            });
            $scope.labelOptions = availableLabels
                .map((i) => ({label: i.name, value: i.id}));
            $scope.$emit("choicesReadyVerbosity");

            function sync_playbook_select2() {
                CreateSelect2({
                    element:'#playbook-select',
                    addNew: true,
                    multiple: false,
                    scope: $scope,
                    options: 'playbook_options',
                    model: 'playbook'
                });
            }

            function sync_webhook_service_select2() {
                CreateSelect2({
                    element:'#webhook-service-select',
                    addNew: false,
                    multiple: false,
                    scope: $scope,
                    options: 'webhook_service_options',
                    model: 'webhook_service'
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
                            .then(({data}) => {
                                var i, opts = [];
                                for (i = 0; i < data.length; i++) {
                                    opts.push(data[i]);
                                }
                                if ($scope.playbook && opts.indexOf($scope.playbook) === -1) {
                                    opts.push($scope.playbook);
                                }
                                $scope.playbook_options = opts;
                                sync_playbook_select2();
                                Wait('stop');
                            })
                            .catch(({data, status}) => {
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
                if ((oldValue !== newValue || (oldValue === undefined && newValue === undefined)) && !Empty($scope.project)) {
                    Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
                    Rest.get()
                        .then(({data}) => {
                            $scope.allow_branch_override = data.allow_override;
                            $scope.allow_playbook_selection = true;
                            selectPlaybook('force_load');

                            var msg;
                            switch (data.status) {
                            case 'failed':
                                msg = `<div>${i18n._('The Project selected has a status of')} \"${i18n._('failed')}\". ${i18n._('You must run a successful update before you can select a playbook. You will not be able to save this Job Template without a valid playbook.')}</div>`;
                                break;
                            case 'never updated':
                                msg = `<div>${i18n._('The Project selected has a status of')} \"${i18n._('never updated')}\". ${i18n._('You must run a successful update before you can select a playbook. You will not be able to save this Job Template without a valid playbook.')}</div>`;
                                break;
                            case 'missing':
                                msg = `<div>${i18n._('The selected project has a status of')} \"${i18n._('missing')}\". ${i18n._('Please check the server and make sure the directory exists and file permissions are set correctly.')}</div>`;
                                break;
                            }
                            if (msg) {
                                Alert(i18n._('Warning'), msg, 'alert-info alert-info--noTextTransform', null, null, null, null, true);
                            }
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                msg: 'Failed to get project ' + $scope.project + '. GET returned status: ' + status });
                        });
                } else {
                    $scope.allow_playbook_selection = false;
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
                            fld !== 'playbook' && fld !== 'custom_virtualenv' && $scope[fld]) {
                            data[fld] = $scope[fld].value;
                        }
                        else if(form.fields[fld].type === 'checkbox_group') {
                            // Loop across the checkboxes
                            for(var i=0; i<form.fields[fld].fields.length; i++) {
                                data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                            }
                        }
                        else {
                            if (fld !== 'extra_vars' &&
                                fld !== 'survey' &&
                                fld !== 'forks') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }
                    data.forks = $scope.forks || 0;
                    data.ask_diff_mode_on_launch = $scope.ask_diff_mode_on_launch ? $scope.ask_diff_mode_on_launch : false;
                    data.ask_scm_branch_on_launch = $scope.ask_scm_branch_on_launch ? $scope.ask_scm_branch_on_launch : false;
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

                    // drop legacy 'credential' and 'vault_credential' keys from the creation request as they will
                    // be provided to the related credentials endpoint by the template save success handler.
                    delete data.credential;
                    delete data.vault_credential;
                    delete data.webhook_url;
                    delete data.webhook_key;
                    data.webhook_credential = $scope.webhookCredential.id;

                    data.extra_vars = ToJSON($scope.parseType, $scope.extra_vars, true);

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
                                .then(({data}) => {
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
                                                    .then(() => {
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

                                            MultiCredentialService
                                                .saveRelated(data, $scope.multiCredential.selectedCredentials)
                                                .then(() => saveCompleted(data.id));
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

            let handleLabelCount = () => {
                /**
                 * This block of code specifically handles the client-side validation of the `labels` field.
                 * Due to it's detached nature in relation to the other job template fields, we must
                 * validate this field client-side in order to avoid the edge case where a user can make a
                 * successful POST to the `job_templates` endpoint but however encounter a 200 error from
                 * the `labels` endpoint due to a character limit.
                 *
                 * We leverage two of select2's available events, `select` and `unselect`, to detect when the user
                 * has either added or removed a label. From there, we set a flag and do simple string length
                 * checks to make sure a label's chacacter count remains under 512. Otherwise, we disable the "Save" button
                 * by invalidating the field and inform the user of the error.
                */


                $scope.job_template_labels_isValid = true;
                const maxCount = 512;
                const jt_label_id = 'job_template_labels';

                // Detect when a new label is added
                $(`#${jt_label_id}`).on('select2:select', (e) => {
                    const { text } = e.params.data;

                    // If the character count of an added label is greater than 512, we set `labels` field as invalid
                    if (text.length > maxCount) {
                        $scope.job_template_form.labels.$setValidity(`${jt_label_id}`, false);
                        $scope.job_template_labels_isValid = false;
                    }
                });

                // Detect when a label is removed
                $(`#${jt_label_id}`).on('select2:unselect', (e) => {
                    const { text } = e.params.data;

                    /* If the character count of a removed label is greater than 512 AND the field is currently marked
                       as invalid, we set it back to valid */
                    if (text.length > maxCount && $scope.job_template_form.labels.$error) {
                        $scope.job_template_form.labels.$setValidity(`${jt_label_id}`, true);
                        $scope.job_template_labels_isValid = true;
                    }
                });
            };

            handleLabelCount();
        }
    ];
