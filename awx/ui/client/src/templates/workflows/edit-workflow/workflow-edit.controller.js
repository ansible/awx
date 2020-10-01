/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', '$stateParams', 'WorkflowForm', 'GenerateForm', 'Alert',
    'ProcessErrors', 'GetBasePath', '$q', 'ParseTypeChange',
    'Wait', 'Empty', 'ToJSON', 'initSurvey', '$state', 'CreateSelect2',
    'ParseVariableString', 'TemplatesService', 'Rest', 'ToggleNotification',
    'OrgAdminLookup', 'availableLabels', 'selectedLabels', 'workflowJobTemplateData', 'i18n',
    'workflowLaunch', '$transitions', 'WorkflowJobTemplateModel', 'Inventory', 'isNotificationAdmin', 'webhookKey', '$compile', '$location', 'GetChoices',
    function($scope, $stateParams, WorkflowForm, GenerateForm, Alert,
        ProcessErrors, GetBasePath, $q, ParseTypeChange, Wait, Empty,
        ToJSON, SurveyControllerInit, $state, CreateSelect2, ParseVariableString,
        TemplatesService, Rest, ToggleNotification, OrgAdminLookup, availableLabels, selectedLabels, workflowJobTemplateData, i18n,
        workflowLaunch, $transitions, WorkflowJobTemplate, Inventory, isNotificationAdmin, webhookKey, $compile, $location, GetChoices
    ) {

        // To toggle notifications a user needs to have a read role on the WFJT
        // _and_ have at least a notification template admin role on an org.
        // If the user has gotten this far it's safe to say they have
        // at least read access to the WFJT
        $scope.sufficientRoleForNotifToggle = isNotificationAdmin;
        $scope.sufficientRoleForNotif =  isNotificationAdmin || $scope.user_is_system_auditor;
        $scope.missingTemplates = _.has(workflowLaunch, 'node_templates_missing') && workflowLaunch.node_templates_missing.length > 0 ? true : false;

        const criteriaObj = {
            from: (state) => state.name === 'templates.editWorkflowJobTemplate.workflowMaker',
            to: (state) => state.name === 'templates.editWorkflowJobTemplate'
        };

        $transitions.onSuccess(criteriaObj, function() {
            if ($scope.missingTemplates) {
                // Go out and check the new launch response to see if the user has fixed the
                // missing node templates

                let workflowJobTemplate = new WorkflowJobTemplate();

                workflowJobTemplate.getLaunch($stateParams.workflow_job_template_id)
                    .then(({data}) => {
                        $scope.missingTemplates = _.has(data, 'node_templates_missing') && data.node_templates_missing.length > 0 ? true : false;
                    });
            }
        });

        // Inject dynamic view
        let form = WorkflowForm(),
            generator = GenerateForm,
            id = $stateParams.workflow_job_template_id;

        $scope.mode = 'edit';
        $scope.parseType = 'yaml';
        $scope.includeWorkflowMaker = false;
        $scope.ask_inventory_on_launch = workflowJobTemplateData.ask_inventory_on_launch;
        $scope.ask_limit_on_launch = workflowJobTemplateData.ask_limit_on_launch;
        $scope.ask_scm_branch_on_launch = workflowJobTemplateData.ask_scm_branch_on_launch;
        $scope.ask_variables_on_launch = (workflowJobTemplateData.ask_variables_on_launch) ? true : false;

        if (Inventory){
            $scope.inventory = Inventory.id;
            $scope.inventory_name = Inventory.name;
        }

        $scope.webhook_service_options = null;
        $scope.webhook_service = workflowJobTemplateData.webhook_service;
        $scope.webhook_url = '';
        $scope.webhook_url_help = i18n._('Webhook services can launch jobs with this job template by making a POST request to this URL.');
        $scope.webhook_key_help = i18n._('Webhook services can use this as a shared secret.');
        $scope.currentlySavedWebhookKey = webhookKey;
        $scope.webhook_key = webhookKey;

        // populate webhook service choices
        GetChoices({
            scope: $scope,
            url: GetBasePath('workflow_job_templates'),
            field: 'webhook_service',
            variable: 'webhook_service_options',
        });

        // set initial val for webhook checkbox
        if (workflowJobTemplateData.webhook_service) {
            $scope.enable_webhook = true;
        } else {
            $scope.enable_webhook = false;
        }

        // set domain / base url
        $scope.baseURL = $location.protocol() + '://' + $location.host() + (($location.port()) ? ':' + $location.port() : '');

        //
        // webhook credential - all handlers, dynamic state, etc. live here
        //

        $scope.webhookCredential = {
            id: _.get(workflowJobTemplateData, ['summary_fields', 'webhook_credential', 'id']),
            name: _.get(workflowJobTemplateData, ['summary_fields', 'webhook_credential', 'name']),
            isModalOpen: false,
            isModalReady: false,
            modalSelectedId: null,
            modalSelectedName: null,
            modalBaseParams: {
                order_by: 'name',
                page_size: 5,
                credential_type__namespace: `${workflowJobTemplateData.webhook_service}_token`,
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
            Rest.setUrl(workflowJobTemplateData.related.webhook_key);
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
                $scope.webhook_url = `${$scope.baseURL}${workflowJobTemplateData.url}${newServiceValue}/`;
                $scope.enable_webhook = true;
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
                    if (newServiceValue === workflowJobTemplateData.webhook_service) {
                        $scope.webhook_key = $scope.currentlySavedWebhookKey;
                    } else {
                        $scope.webhook_key = i18n._('A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE');
                    }
                }
            }
        });

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

        $scope.openWorkflowMaker = function() {
            $state.go('templates.editWorkflowJobTemplate.workflowMaker');
        };

        $scope.formSave = function () {
            let fld, data = {};
            $scope.invalid_survey = false;

            // Can't have a survey enabled without a survey
            if($scope.survey_enabled === true && $scope.survey_exists!==true){
                $scope.survey_enabled = false;
            }

            generator.clearApiErrors($scope);

            Wait('start');

            try {
                for (fld in form.fields) {
                    if(form.fields[fld].type === 'checkbox_group') {
                        // Loop across the checkboxes
                        for(var i=0; i<form.fields[fld].fields.length; i++) {
                            data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                        }
                    } else {
                        data[fld] = $scope[fld];
                    }
                }

                data.ask_inventory_on_launch = Boolean($scope.ask_inventory_on_launch);
                data.ask_limit_on_launch = Boolean($scope.ask_limit_on_launch);
                data.ask_scm_branch_on_launch = Boolean($scope.ask_scm_branch_on_launch);
                data.ask_variables_on_launch = Boolean($scope.ask_variables_on_launch);

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
                $("#workflow_job_template_labels > option").filter("[data-select2-tag=true]").each(function(optionIndex, option) {
                    $("#workflow_job_template_labels").siblings(".select2").first().find(".select2-selection__choice").each(function(labelIndex, label) {
                        if($(option).text() === $(label).attr('title')) {
                            // Mark that the option has a label present so that we can filter by that down below
                            $(option).attr('data-label-is-present', true);
                        }
                    });
                });

                $scope.newLabels = $("#workflow_job_template_labels > option")
                .filter("[data-select2-tag=true]")
                .filter("[data-label-is-present=true]")
                .map((i, val) => ({name: $(val).text()}));


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

                if (data.webhook_service && typeof data.webhook_service === 'object') {
                    data.webhook_service = data.webhook_service.value;
                }

                TemplatesService.updateWorkflowJobTemplate({
                    id: id,
                    data: data
                }).then(function(){

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

                    Rest.setUrl($scope.workflow_job_template_obj.related.labels);

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

                            Rest.setUrl($scope.workflow_job_template_obj.related.labels);

                            var defers = [];
                            for (var i = 0; i < toPost.length; i++) {
                                defers.push(Rest.post(toPost[i]));
                            }
                            $q.all(defers)
                                .then(function() {
                                    $state.go('templates.editWorkflowJobTemplate', {id: id}, {reload: true});
                                });
                        });
                    });

                }, function(error){
                    ProcessErrors($scope, error.data, error.status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to update workflow job template. PUT returned ' +
                        'status: ' + error.status
                    });
                });

            } catch (err) {
                Wait('stop');
                Alert("Error", "Error saving workflow job template. " +
                "Parser returned: " + err);
            }
        };

        $scope.formCancel = function () {
            $state.transitionTo('templates');
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
                url: GetBasePath('workflow_job_templates') + id,
                notifier: notifier,
                column: column,
                callback: 'NotificationRefresh'
            });
        };

        SurveyControllerInit({
            scope: $scope,
            parent_scope: $scope,
            id: id,
            templateType: 'workflow_job_template'
        });

        $scope.labelOptions = availableLabels
            .map((i) => ({label: i.name, value: i.id}));

        var opts = selectedLabels
            .map(i => ({id: i.id + "",
                test: i.name}));

        // Select2-ify the lables input
        CreateSelect2({
            element:'#workflow_job_template_labels',
            multiple: true,
            addNew: true,
            opts
        }).then(() => {
            // updates based on lookups will initially set the form as dirty.
            // we need to set it as pristine when it contains the values given by the api
            // so that we can enable launching when the two are the same
            $scope.workflow_job_template_form.$setPristine();
            // this is used to set the overall form as dirty for the values
            // that don't actually set this internally (lookups, toggles and code mirrors).
            $scope.$watchGroup([
                'organization',
                'inventory',
                'variables'
            ], (val, prevVal) => {
                if (!_.isEqual(val, prevVal)) {
                    $scope.workflow_job_template_form.$setDirty();
                }
            });
        });

        $scope.workflowVisualizerTooltip = i18n._("Click here to open the workflow visualizer.");
        $scope.surveyTooltip = i18n._('Surveys allow users to be prompted at job launch with a series of questions related to the job. This allows for variables to be defined that affect the playbook run at time of launch.');

        $scope.workflow_job_template_obj = workflowJobTemplateData;
        $scope.name = workflowJobTemplateData.name;
        $scope.can_edit = $scope.canAddOrEdit = workflowJobTemplateData.summary_fields.user_capabilities.edit;
        $scope.breadcrumb.workflow_job_template_name = $scope.name;
        let fld, i;
        for (fld in form.fields) {
            if (fld !== 'variables' && fld !== 'survey' && workflowJobTemplateData[fld] !== null && workflowJobTemplateData[fld] !== undefined) {
                if (form.fields[fld].type === 'select') {
                    if ($scope[fld + '_options'] && $scope[fld + '_options'].length > 0) {
                        for (i = 0; i < $scope[fld + '_options'].length; i++) {
                            if (workflowJobTemplateData[fld] === $scope[fld + '_options'][i].value) {
                                $scope[fld] = $scope[fld + '_options'][i];
                            }
                        }
                    } else {
                        $scope[fld] = workflowJobTemplateData[fld];
                    }
                } else {
                    $scope[fld] = workflowJobTemplateData[fld];
                    if(!Empty(workflowJobTemplateData.summary_fields.survey)) {
                        $scope.survey_exists = true;
                    }
                }
            }
            if (fld === 'variables') {
                // Parse extra_vars, converting to YAML.
                $scope.variables = ParseVariableString(workflowJobTemplateData.extra_vars);

                ParseTypeChange({
                    scope: $scope,
                    field_id: 'workflow_job_template_variables',
                    readOnly: !workflowJobTemplateData.summary_fields.user_capabilities.edit
                });
            }
            if (form.fields[fld].type === 'lookup' && workflowJobTemplateData.summary_fields[form.fields[fld].sourceModel]) {
                $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                workflowJobTemplateData.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
            }
            if (form.fields[fld].type === 'checkbox_group') {
                for(var j=0; j<form.fields[fld].fields.length; j++) {
                    $scope[form.fields[fld].fields[j].name] = workflowJobTemplateData[form.fields[fld].fields[j].name];
                }
            }
        }

        if(workflowJobTemplateData.organization) {
            OrgAdminLookup.checkForRoleLevelAdminAccess(workflowJobTemplateData.organization, 'workflow_admin_role')
            .then(function(canEditOrg){
                $scope.canEditOrg = canEditOrg;
            });
        }
        else {
            $scope.canEditOrg = true;
        }

        if(workflowJobTemplateData.inventory) {
            let params = {
              role_level: 'use_role',
              id: workflowJobTemplateData.inventory
            };
            Rest.setUrl(GetBasePath('inventory'));
            Rest.get({ params: params })
              .then(({ data }) => {
                if (data.count && data.count > 0) {
                  $scope.canEditInventory = true;
                } else {
                  $scope.canEditInventory = false;
                }
              })
              .catch(({ data, status }) => {
                ProcessErrors(null, data, status, null, {
                  hdr: 'Error!',
                  msg: 'Failed to get inventory data based on role_level. Return status: ' + status
              });
            });
        }
        else {
            $scope.canEditInventory = true;
        }

        $scope.url = workflowJobTemplateData.url;
        $scope.survey_enabled = workflowJobTemplateData.survey_enabled;

        $scope.includeWorkflowMaker = true;

        $scope.$on('SurveySaved', function() {
            Wait('stop');
            $scope.survey_exists = true;
            $scope.invalid_survey = false;
        });

        let handleLabelCount = () => {
            /**
             * This block of code specifically handles the client-side validation of the `labels` field.
             * Due to it's detached nature in relation to the other job template fields, we must
             * validate this field client-side in order to avoid the edge case where a user can make a
             * successful POST to the `workflow_job_templates` endpoint but however encounter a 200 error from
             * the `labels` endpoint due to a character limit.
             *
             * We leverage two of select2's available events, `select` and `unselect`, to detect when the user
             * has either added or removed a label. From there, we set a flag and do simple string length
             * checks to make sure a label's chacacter count remains under 512. Otherwise, we disable the "Save" button
             * by invalidating the field and inform the user of the error.
            */

            $scope.workflow_job_template_labels_isValid = true;
            const maxCount = 512;
            const wfjt_label_id = 'workflow_job_template_labels';
             // Detect when a new label is added
            $(`#${wfjt_label_id}`).on('select2:select', (e) => {
                const { text } = e.params.data;
                 // If the character count of an added label is greater than 512, we set `labels` field as invalid
                if (text.length > maxCount) {
                    $scope.workflow_job_template_form.labels.$setValidity(`${wfjt_label_id}`, false);
                    $scope.workflow_job_template_labels_isValid = false;
                }
            });
             // Detect when a label is removed
            $(`#${wfjt_label_id}`).on('select2:unselect', (e) => {
                const { text } = e.params.data;
                 /* If the character count of a removed label is greater than 512 AND the field is currently marked
                   as invalid, we set it back to valid */
                if (text.length > maxCount && $scope.workflow_job_template_form.labels.$error) {
                    $scope.workflow_job_template_form.labels.$setValidity(`${wfjt_label_id}`, true);
                    $scope.workflow_job_template_labels_isValid = true;
                }
            });
        };

        handleLabelCount();
    }
];
