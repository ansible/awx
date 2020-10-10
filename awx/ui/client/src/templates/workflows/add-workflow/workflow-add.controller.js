/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', 'WorkflowForm', 'GenerateForm', 'Alert', 'ProcessErrors',
    'Wait', '$state', 'CreateSelect2', 'TemplatesService',
    'ToJSON', 'ParseTypeChange', '$q', 'Rest', 'GetBasePath', 'availableLabels', 'i18n',
    'resolvedModels', 'GetChoices', '$compile',
    function($scope, WorkflowForm, GenerateForm, Alert, ProcessErrors,
    Wait, $state, CreateSelect2, TemplatesService, ToJSON,
    ParseTypeChange, $q, Rest, GetBasePath, availableLabels, i18n,
    resolvedModels, GetChoices, $compile) {

         // Inject dynamic view
         let form = WorkflowForm(),
             generator = GenerateForm;

         const workflowTemplate = resolvedModels[1];

         $scope.canAddOrEdit = workflowTemplate.options('actions.POST') ? true : false;

         $scope.canEditOrg = true;
         $scope.canEditInventory = true;
         $scope.parseType = 'yaml';
         $scope.can_edit = true;
         $scope.disableLaunch = true;
         // apply form definition's default field values
         GenerateForm.applyDefaults(form, $scope);

         // Make the variables textarea look pretty
         ParseTypeChange({
             scope: $scope,
             field_id: 'workflow_job_template_variables',
             onChange: function() {
                 // Make sure the form controller knows there was a change
                 $scope[form.name + '_form'].$setDirty();
             }
         });

         $scope.labelOptions = availableLabels
             .map((i) => ({label: i.name, value: i.id}));

         CreateSelect2({
             element:'#workflow_job_template_labels',
             multiple: true,
             addNew: true
         });

         $scope.workflowEditorTooltip = i18n._("Please save before defining the workflow graph.");
         $scope.surveyTooltip = i18n._('Please save before adding a survey to this workflow.');

        $scope.webhook_service_options = null;

        // populate webhook service choices
        GetChoices({
            scope: $scope,
            url: GetBasePath('workflow_job_templates'),
            field: 'webhook_service',
            variable: 'webhook_service_options',
        });

        // set initial val for webhook checkbox
        $scope.enable_webhook = false;

        //
        // webhook credential - all handlers, dynamic state, etc. live here
        //

        $scope.webhookCredential = {
            id: null,
            name: null,
            isModalOpen: false,
            isModalReady: false,
            modalSelectedId: null,
            modalSelectedName: null,
            modalBaseParams: {
                order_by: 'name',
                page_size: 5,
                credential_type__namespace: null,
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

         $scope.formSave = function () {
             let fld, data = {};

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
                 data.ask_variables_on_launch = Boolean($scope.ask_variables_on_launch);
                 data.ask_limit_on_launch = Boolean($scope.ask_limit_on_launch);
                 data.ask_scm_branch_on_launch = Boolean($scope.ask_scm_branch_on_launch);

                 data.extra_vars = ToJSON($scope.parseType,
                     $scope.variables, true);

                 // The idea here is that we want to find the new option elements that also have a label that exists in the dom
                 $("#workflow_job_template_labels > option")
                    .filter("[data-select2-tag=true]")
                    .each(function(optionIndex, option) {
                        $("#workflow_job_template_labels")
                            .siblings(".select2").first().find(".select2-selection__choice")
                            .each(function(labelIndex, label) {
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

                 TemplatesService.createWorkflowJobTemplate(data)
                     .then(function(data) {

                         let orgDefer = $q.defer();
                         let associationDefer = $q.defer();

                         Rest.setUrl(data.data.related.labels);

                         let currentLabels = Rest.get()
                             .then(function(data) {
                                 return data.data.results
                                     .map(val => val.id);
                             });

                         currentLabels.then(function (current) {
                             let labelsToAdd = ($scope.labels || [])
                                 .map(val => val.value);
                             let labelsToDisassociate = current
                                 .filter(val => labelsToAdd
                                     .indexOf(val) === -1)
                                 .map(val => ({id: val, disassociate: true}));
                             let labelsToAssociate = labelsToAdd
                                 .filter(val => current
                                     .indexOf(val) === -1)
                                 .map(val => ({id: val, associate: true}));
                             let pass = labelsToDisassociate
                                 .concat(labelsToAssociate);
                             associationDefer.resolve(pass);
                         });

                         Rest.setUrl(GetBasePath("organizations"));
                         Rest.get()
                             .then(({data}) => {
                                 orgDefer.resolve(data.results[0].id);
                             });

                         orgDefer.promise.then(function(orgId) {
                             let toPost = [];
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

                                 Rest.setUrl(data.data.related.labels);

                                 let defers = [];
                                 for (let i = 0; i < toPost.length; i++) {
                                     defers.push(Rest.post(toPost[i]));
                                 }
                                 $q.all(defers)
                                     .then(function() {
                                         // If we follow the same pattern as job templates then the survey logic will go here
                                         $state.go('templates.editWorkflowJobTemplate.workflowMaker', { workflow_job_template_id: data.data.id }, { reload: true });
                                     });
                             });
                         });

                     }, function (error) {
                         ProcessErrors($scope, error.data, error.status, form,
                             {
                                 hdr: 'Error!',
                                 msg: 'Failed to add new workflow. ' +
                                 'POST returned status: ' +
                                 error.status
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
