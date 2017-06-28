/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', 'WorkflowForm', 'GenerateForm', 'Alert', 'ProcessErrors',
    'Wait', '$state', 'CreateSelect2', 'TemplatesService',
    'ToJSON', 'ParseTypeChange', '$q', 'Rest', 'GetBasePath', 'availableLabels', 'i18n',
    function($scope, WorkflowForm, GenerateForm, Alert, ProcessErrors,
    Wait, $state, CreateSelect2, TemplatesService, ToJSON,
    ParseTypeChange, $q, Rest, GetBasePath, availableLabels, i18n) {

         // Inject dynamic view
         let form = WorkflowForm(),
             generator = GenerateForm;

         function init() {
             $scope.canEditOrg = true;
             $scope.parseType = 'yaml';
             $scope.can_edit = true;
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
         }

         $scope.formSave = function () {
             let fld, data = {};

             generator.clearApiErrors($scope);

             Wait('start');

             try {
                 for (fld in form.fields) {
                     data[fld] = $scope[fld];
                 }

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
                             .success(function(data) {
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

                                         $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: data.data.id}, {reload: true});
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

         init();
     }
    ];
