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
    [   '$filter', '$scope',
        '$stateParams', 'JobTemplateForm', 'GenerateForm',
        'Rest', 'Alert',  'ProcessErrors', 'GetBasePath', 'hashSetup',
        'ParseTypeChange', 'Wait', 'selectedLabels', 'i18n',
        'Empty', 'ToJSON', 'GetChoices', 'CallbackHelpInit',
        'initSurvey', '$state', 'CreateSelect2', 'isNotificationAdmin',
        'ToggleNotification','$q', 'InstanceGroupsService', 'InstanceGroupsData',
        'MultiCredentialService', 'availableLabels', 'projectGetPermissionDenied',
        'inventoryGetPermissionDenied', 'jobTemplateData', 'ParseVariableString', 'ConfigData', '$compile', 'webhookKey',
        function(
            $filter, $scope,
            $stateParams, JobTemplateForm, GenerateForm, Rest, Alert,
            ProcessErrors, GetBasePath, hashSetup,
            ParseTypeChange, Wait, selectedLabels, i18n,
            Empty, ToJSON, GetChoices, CallbackHelpInit,
            SurveyControllerInit, $state, CreateSelect2, isNotificationAdmin,
            ToggleNotification, $q, InstanceGroupsService, InstanceGroupsData,
            MultiCredentialService, availableLabels, projectGetPermissionDenied,
            inventoryGetPermissionDenied, jobTemplateData, ParseVariableString, ConfigData, $compile, webhookKey
        ) {

            $scope.$watch('job_template_obj.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAddJobTemplate = false;
                }
            });

            let defaultUrl = GetBasePath('job_templates'),
                generator = GenerateForm,
                form = JobTemplateForm(),
                main = {},
                id = $stateParams.job_template_id,
                callback,
                choicesCount = 0,
                instance_group_url = defaultUrl + id + '/instance_groups',
                select2LoadDefer = [],
                launchHasBeenEnabled = false;

            init();
            function init() {

                CallbackHelpInit({ scope: $scope });

                // To toggle notifications a user needs to have a read role on the JT
                // _and_ have at least a notification template admin role on an org.
                // If the user has gotten this far it's safe to say they have
                // at least read access to the JT
                $scope.sufficientRoleForNotifToggle = isNotificationAdmin;
                $scope.sufficientRoleForNotif =  isNotificationAdmin || $scope.user_is_system_auditor;
                $scope.playbook_options = null;
                $scope.webhook_service_options = null;
                $scope.playbook = null;
                $scope.webhook_service = jobTemplateData.webhook_service;
                $scope.webhook_url = '';
                $scope.mode = 'edit';
                $scope.parseType = 'yaml';
                $scope.showJobType = false;
                $scope.instance_groups = InstanceGroupsData;
                $scope.credentialNotPresent = false;
                $scope.surveyTooltip = i18n._('Surveys allow users to be prompted at job launch with a series of questions related to the job. This allows for variables to be defined that affect the playbook run at time of launch.');
                $scope.job_tag_options = [];
                $scope.skip_tag_options = [];
                const virtualEnvs = ConfigData.custom_virtualenvs || [];
                $scope.custom_virtualenvs_options = virtualEnvs;
                $scope.webhook_url_help = i18n._('Webhook services can launch jobs with this job template by making a POST request to this URL.');
                $scope.webhook_key_help = i18n._('Webhook services can use this as a shared secret.');

                $scope.currentlySavedWebhookKey = webhookKey;
                $scope.webhook_key = webhookKey;

                //
                // webhook credential - all handlers, dynamic state, etc. live here
                //

                $scope.webhookCredential = {
                    id: _.get(jobTemplateData, ['summary_fields', 'webhook_credential', 'id']),
                    name: _.get(jobTemplateData, ['summary_fields', 'webhook_credential', 'name']),
                    isModalOpen: false,
                    isModalReady: false,
                    modalSelectedId: null,
                    modalSelectedName: null,
                    modalBaseParams: {
                        order_by: 'name',
                        page_size: 5,
                        credential_type__namespace: `${jobTemplateData.webhook_service}_token`,
                    },
                    modalTitle: i18n._('Select Webhook Credential'),
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

                $scope.handleWebhookKeyButtonClick = () => {
                    Rest.setUrl(jobTemplateData.related.webhook_key);
                    Wait('start');
                    Rest.post({})
                        .then(({ data }) => {
                            $scope.currentlySavedWebhookKey = data.webhook_key;
                            $scope.webhook_key = data.webhook_key;
                        })
                        .catch(({ data }) => {
                            const errorMsg = `Failed to generate new webhook key. POST returned status: ${status}`;
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: errorMsg });
                        })
                        .finally(() => {
                            Wait('stop');
                        });
                };

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
                    if (newServiceValue) {
                        $scope.webhook_url = `${$scope.callback_server_path}${jobTemplateData.url}${newServiceValue}/`;
                    } else {
                        $scope.webhook_url = '';
                        $scope.webhook_key = '';
                    }
                    if (newServiceValue !== oldServiceValue || newServiceValue === newValue) {
                        $scope.webhook_service = { value: newServiceValue };
                        sync_webhook_service_select2();
                        $scope.webhookCredential.modalBaseParams.credential_type__namespace = newServiceValue ?
                            `${newServiceValue}_token` : null;
                        if (newServiceValue !== newValue || newValue === null) {
                            $scope.webhookCredential.id = null;
                            $scope.webhookCredential.name = null;
                        }
                        if (newServiceValue !== newValue) {
                            if (newServiceValue === jobTemplateData.webhook_service) {
                                $scope.webhook_key = $scope.currentlySavedWebhookKey;
                            } else {
                                $scope.webhook_key = i18n._('A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE');
                            }
                        }
                    }
                });

                $scope.$watch('verbosity', sync_verbosity_select2);
                $scope.$watch('job_type', sync_job_type_select2);

                SurveyControllerInit({
                    scope: $scope,
                    parent_scope: $scope,
                    id: id,
                    templateType: 'job_template'
                });

                $scope.$watch('project', function (newValue, oldValue) {
                    if (newValue !== oldValue) {
                        if (oldValue) {
                            $scope.scm_branch = null;
                            $scope.ask_scm_branch_on_launch = false;
                        }
                        
                        var url;
                        if ($scope.playbook) {
                            $scope.playbook_options = [$scope.playbook];
                        }

                        if (!Empty($scope.project)) {
                            // If a project exists, show its playbooks.
                            $scope.allow_playbook_selection = true;
                        }

                        if (!Empty($scope.project) && $scope.job_template_obj.summary_fields.user_capabilities.edit) {
                            let promises = [];
                            url = GetBasePath('projects') + $scope.project + '/playbooks/';
                            Wait('start');
                            Rest.setUrl(url);
                            promises.push(Rest.get()
                                .then(({data}) => {
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
                                    if ($scope.playbook && $scope.playbook_options.indexOf($scope.playbook) === -1) {
                                        $scope.playbook_options.push($scope.playbook);
                                    }
                                    $scope.playbookNotFound = playbookNotFound;
                                    sync_playbook_select2();
                                    if ($scope.playbook) {
                                        jobTemplateLoadFinished();
                                    }
                                })
                                .catch( (error) => {
                                    if (error.status === 403) {
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
                                .then(({data}) => {
                                    $scope.allow_branch_override = data.allow_override;
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
                                .catch(({data, status}) => {
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
                                })
                                .catch(({data, status}) => {
                                    ProcessErrors($scope, data, status, null, {
                                        hdr: 'Error!',
                                        msg: 'Call failed. Returned status: ' + status
                                    });
                                });
                        }
                    }
                });
            }

            callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };

            function sync_playbook_select2() {
                select2LoadDefer.push(CreateSelect2({
                    element:'#playbook-select',
                    addNew: true,
                    multiple: false,
                    scope: $scope,
                    options: 'playbook_options',
                    model: 'playbook'
                }));
            }

            function sync_verbosity_select2(newValue) {
                if (newValue === 0 || (newValue && typeof newValue !== 'object')) {
                    $scope.verbosity = { value: newValue };
                    return;
                }
                select2LoadDefer.push(CreateSelect2({
                    element:'#job_template_verbosity',
                    multiple: false,
                    scope: $scope,
                    model: 'verbosity',
                    options: 'verbosity_options',
                }));
            }

            function sync_job_type_select2(newValue) {
                if (newValue === 0 || (newValue && typeof newValue !== 'object')) {
                    $scope.job_type = { value: newValue };
                    return;
                }
                select2LoadDefer.push(CreateSelect2({
                    element:'#job_template_job_type',
                    multiple: false,
                    scope: $scope,
                    model: 'job_type',
                    options: 'job_type_options',
                }));
            }

            function sync_webhook_service_select2() {
                select2LoadDefer.push(CreateSelect2({
                    element:'#webhook-service-select',
                    addNew: false,
                    multiple: false,
                    scope: $scope,
                    options: 'webhook_service_options',
                    model: 'webhook_service'
                }));
            }

            function jobTemplateLoadFinished(){
                select2LoadDefer.push(CreateSelect2({
                    element:'#job_template_job_type',
                    multiple: false
                }));

                select2LoadDefer.push(CreateSelect2({
                    element:'#job_template_job_tags',
                    multiple: true,
                    addNew: true
                }));

                select2LoadDefer.push(CreateSelect2({
                    element:'#job_template_skip_tags',
                    multiple: true,
                    addNew: true
                }));

                select2LoadDefer.push(CreateSelect2({
                    element: '#job_template_custom_virtualenv',
                    multiple: false,
                    opts: $scope.custom_virtualenvs_options
                }));
                select2LoadDefer.push(CreateSelect2({
                    element:'#webhook-service-select',
                    addNew: false,
                    multiple: false,
                    scope: $scope,
                    options: 'webhook_service_options',
                    model: 'webhook_service'
                }));

                if (!launchHasBeenEnabled) {
                    $q.all(select2LoadDefer).then(() => {
                        // updates based on lookups will initially set the form as dirty.
                        // we need to set it as pristine when it contains the values given by the api
                        // so that we can enable launching when the two are the same
                        $scope.job_template_form.$setPristine();
                        // this is used to set the overall form as dirty for the values
                        // that don't actually set this internally (lookups, toggles and code mirrors).
                        $scope.$watchCollection('multiCredential.selectedCredentials', (val, prevVal) => {
                            if (!_.isEqual(val, prevVal)) {
                                $scope.job_template_form.$setDirty();
                            }
                        });
                        $scope.$watchGroup([
                            'inventory',
                            'project',
                            'extra_vars',
                            'diff_mode',
                            'instance_groups'
                        ], (val, prevVal) => {
                            if (!_.isEqual(val, prevVal)) {
                                $scope.job_template_form.$setDirty();
                            }
                        });
                    });
                }
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
            $scope.jobTemplateLoadedRemove = $scope.$on('jobTemplateLoaded', function (e, mainObject) {
                var dft;

                main = mainObject;

                dft = ($scope.host_config_key === "" || $scope.host_config_key === null) ? false : true;
                hashSetup({
                    scope: $scope,
                    main: main,
                    check_field: 'allow_callbacks',
                    default_val: dft
                });

                // set initial vals for webhook checkbox
                if (jobTemplateData.webhook_service) {
                    $scope.enable_webhook = true;
                    main.enable_webhook = true;
                } else {
                    $scope.enable_webhook = false;
                    main.enable_webhook = false;
                }

                ParseTypeChange({
                    scope: $scope,
                    field_id: 'extra_vars',
                    variable: 'extra_vars',
                    onChange: callback,
                    readOnly: !$scope.job_template_obj.summary_fields.user_capabilities.edit
                });
                jobTemplateLoadFinished();
                launchHasBeenEnabled = true;
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
                $scope.breadcrumb.job_template_name = jobTemplateData.name;
                var fld, i;
                for (fld in form.fields) {
                    if (fld !== 'extra_vars' && fld !== 'survey' && jobTemplateData[fld] !== null && jobTemplateData[fld] !== undefined) {
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
                        main[fld] = $scope[fld];
                    }
                    if (fld === 'extra_vars') {
                        // Parse extra_vars, converting to YAML.
                        $scope.extra_vars = ParseVariableString(jobTemplateData.extra_vars);
                        main.extra_vars = $scope.extra_vars;
                    }
                    if (form.fields[fld].type === 'lookup' && jobTemplateData.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            jobTemplateData.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        main[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
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
                main.ask_variables_on_launch = $scope.ask_variables_on_launch;

                $scope.ask_verbosity_on_launch = (jobTemplateData.ask_verbosity_on_launch) ? true : false;
                main.ask_verbosity_on_launch = $scope.ask_verbosity_on_launch;

                $scope.ask_limit_on_launch = (jobTemplateData.ask_limit_on_launch) ? true : false;
                main.ask_limit_on_launch = $scope.ask_limit_on_launch;

                $scope.ask_tags_on_launch = (jobTemplateData.ask_tags_on_launch) ? true : false;
                main.ask_tags_on_launch = $scope.ask_tags_on_launch;

                $scope.ask_skip_tags_on_launch = (jobTemplateData.ask_skip_tags_on_launch) ? true : false;
                main.ask_skip_tags_on_launch = $scope.ask_skip_tags_on_launch;

                $scope.ask_diff_mode_on_launch = (jobTemplateData.ask_diff_mode_on_launch) ? true : false;
                main.ask_diff_mode_on_launch = $scope.ask_diff_mode_on_launch;

                $scope.ask_scm_branch_on_launch = (jobTemplateData.ask_scm_branch_on_launch) ? true : false;
                main.ask_scm_branch_on_launch = $scope.ask_scm_branch_on_launch;

                $scope.job_tag_options = (jobTemplateData.job_tags) ? jobTemplateData.job_tags.split(',')
                    .map((i) => ({name: i, label: i, value: i})) : [];
                $scope.job_tags = $scope.job_tag_options;
                main.job_tags = $scope.job_tags;

                $scope.skip_tag_options = (jobTemplateData.skip_tags) ? jobTemplateData.skip_tags.split(',')
                    .map((i) => ({name: i, label: i, value: i})) : [];
                $scope.skip_tags = $scope.skip_tag_options;
                main.skip_tags = $scope.skip_tags;

                $scope.ask_job_type_on_launch = (jobTemplateData.ask_job_type_on_launch) ? true : false;
                main.ask_job_type_on_launch = $scope.ask_job_type_on_launch;

                $scope.ask_inventory_on_launch = (jobTemplateData.ask_inventory_on_launch) ? true : false;
                main.ask_inventory_on_launch = $scope.ask_inventory_on_launch;

                $scope.ask_credential_on_launch = (jobTemplateData.ask_credential_on_launch) ? true : false;
                main.ask_credential_on_launch = $scope.ask_credential_on_launch;

                if (jobTemplateData.host_config_key) {
                    $scope.example_config_key = jobTemplateData.host_config_key;
                }
                $scope.example_template_id = id;
                $scope.setCallbackHelp();

                $scope.callback_url = $scope.callback_server_path + ((jobTemplateData.related.callback) ? jobTemplateData.related.callback :
                GetBasePath('job_templates') + id + '/callback/');
                main.callback_url = $scope.callback_url;

                $scope.can_edit = jobTemplateData.summary_fields.user_capabilities.edit;

                const multiCredential = {};
                const credentialTypesPromise = MultiCredentialService.getCredentialTypes()
                    .then(({ data }) => {
                        multiCredential.credentialTypes = data.results;
                    });
                const multiCredentialPromises = [credentialTypesPromise];

                if ($scope.can_edit) {
                    const selectedCredentialsPromise =  MultiCredentialService
                        .getRelated(jobTemplateData, { permitted: [403] })
                        .then(({ data, status }) => {
                            if (status === 403) {
                                $scope.canGetAllRelatedResources = false;
                                multiCredential.selectedCredentials = _.get(jobTemplateData, 'summary_fields.credentials');
                            } else {
                                $scope.canGetAllRelatedResources = !projectGetPermissionDenied && !inventoryGetPermissionDenied;
                                multiCredential.selectedCredentials = data.results;
                            }
                        });

                    multiCredentialPromises.push(selectedCredentialsPromise);
                } else {
                    $scope.canGetAllRelatedResources = false;
                    multiCredential.selectedCredentials = _.get(jobTemplateData, 'summary_fields.credentials');
                }

                $q.all(multiCredentialPromises)
                    .then(() => {
                        $scope.multiCredential = multiCredential;
                        $scope.$emit('jobTemplateLoaded', main);
                    });
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

            GetChoices({
                scope: $scope,
                url: defaultUrl,
                field: 'webhook_service',
                variable: 'webhook_service_options',
                callback: 'choicesReady'
            });

            $scope.labelOptions = availableLabels
                .map((i) => ({label: i.name, value: i.id}));

            var opts = selectedLabels
                .map(i => ({id: i.id + "",
                    test: i.name}));

            select2LoadDefer.push(CreateSelect2({
                element:'#job_template_labels',
                multiple: true,
                addNew: true,
                opts: opts
            }));

            $scope.$emit("choicesReady");

            function saveCompleted() {
                $state.go($state.current, {}, {reload: true});
            }

            if ($scope.removeTemplateSaveSuccess) {
                $scope.removeTemplateSaveSuccess();
            }
            $scope.removeTemplateSaveSuccess = $scope.$on('templateSaveSuccess', function(e, data) {

                if (data.related &&
                    data.related.callback) {
                    Alert('Callback URL',
`Host callbacks are enabled for this template. The callback URL is:
<p style=\"padding: 10px 0;\">
    <strong>
        ${$scope.callback_server_path}${data.related.callback}
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

                var credDefer = MultiCredentialService
                    .saveRelated(jobTemplateData, $scope.multiCredential.selectedCredentials);

                const instanceGroupDefer = InstanceGroupsService.editInstanceGroups(instance_group_url, $scope.instance_groups)
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
                        .then(({data}) => {
                            if (data.next) {
                                getNext(data, arr.concat(data.results), resolve);
                            } else {
                                resolve.resolve(arr.concat(data.results));
                            }
                        });
                };

                Rest.setUrl(data.related.labels);

                Rest.get()
                    .then(({data}) => {
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

                        var defers = [credDefer, instanceGroupDefer];
                        for (var i = 0; i < toPost.length; i++) {
                            defers.push(Rest.post(toPost[i]));
                        }
                        $q.all(defers)
                            .then(function() {
                                Wait('stop');
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
                            fld !== 'playbook' && fld !== 'custom_virtualenv' && $scope[fld]) {
                            data[fld] = $scope[fld].value;
                        }
                        else if(form.fields[fld].type === 'checkbox_group') {
                            // Loop across the checkboxes
                            for(var i=0; i<form.fields[fld].fields.length; i++) {
                                data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                            }
                        } else if (fld === 'scm_branch' && $scope.allow_branch_override) {
                            data[fld] = $scope[fld];
                        } else {
                            if (fld !== 'extra_vars' &&
                                fld !== 'survey' &&
                                fld !== 'forks') {
                                data[fld] = $scope[fld];
                            }
                        }
                    }

                    data.forks = $scope.forks || 0;
                    data.ask_diff_mode_on_launch = $scope.ask_diff_mode_on_launch ? $scope.ask_diff_mode_on_launch : false;
                    data.ask_scm_branch_on_launch = $scope.ask_scm_branch_on_launch && $scope.allow_branch_override ? $scope.ask_scm_branch_on_launch : false;
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

                    data.extra_vars = ToJSON($scope.parseType,
                        $scope.extra_vars, true);

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

                    delete data.webhook_url;
                    delete data.webhook_key;
                    delete data.enable_webhook;
                    data.webhook_credential = $scope.webhookCredential.id;

                    if (!data.webhook_service) {
                        data.webhook_credential = null;
                    }

                    if (!$scope.enable_webhook) {
                        data.webhook_service = '';
                        data.webhook_credential = null;
                    }

                    Rest.setUrl(defaultUrl + $state.params.job_template_id);
                    Rest.patch(data)
                        .then(({data}) => {
                            $scope.$emit('templateSaveSuccess', data);
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                msg: 'Failed to update job template. PATCH returned status: ' + status });
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
