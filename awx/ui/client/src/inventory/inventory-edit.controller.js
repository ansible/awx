/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

import '../job-templates/main';

function InventoriesEdit($scope, $rootScope, $compile, $location,
    $log, $stateParams, InventoryForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, generateList, OrganizationList, SearchInit,
    PaginateInit, LookUpInit, GetBasePath, ParseTypeChange, Wait, ToJSON,
    ParseVariableString, RelatedSearchInit, RelatedPaginateInit,
    Prompt, PlaybookRun, CreateDialog, deleteJobTemplate, $state) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm(),
        generator = GenerateForm,
        inventory_id = $stateParams.inventory_id,
        master = {},
        fld, json_data, data,
        relatedSets = {};

    form.well = true;
    form.formLabelSize = null;
    form.formFieldSize = null;
    $scope.inventory_id = inventory_id;
    generator.inject(form, { mode: 'edit', related: true, scope: $scope });

    generator.reset();


    // After the project is loaded, retrieve each related set
    if ($scope.inventoryLoadedRemove) {
        $scope.inventoryLoadedRemove();
    }
    $scope.projectLoadedRemove = $scope.$on('inventoryLoaded', function () {
        var set;
        for (set in relatedSets) {
            $scope.search(relatedSets[set].iterator);
        }
    });

    Wait('start');
    Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
    Rest.get()
        .success(function (data) {
            var fld;
            for (fld in form.fields) {
                if (fld === 'variables') {
                    $scope.variables = ParseVariableString(data.variables);
                    master.variables = $scope.variables;
                } else if (fld === 'inventory_name') {
                  $scope[fld] = data.name;
                    master[fld] = $scope[fld];
                } else if (fld === 'inventory_description') {
                  $scope[fld] = data.description;
                    master[fld] = $scope[fld];
                } else if (data[fld]) {
                  $scope[fld] = data[fld];
                    master[fld] = $scope[fld];
                }
                if (form.fields[fld].sourceModel && data.summary_fields &&
                    data.summary_fields[form.fields[fld].sourceModel]) {
                      $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                }
            }
            relatedSets = form.relatedSets(data.related);

            // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
            RelatedSearchInit({
                scope: $scope,
                form: form,
                relatedSets: relatedSets
            });
            RelatedPaginateInit({
                scope: $scope,
                relatedSets: relatedSets
            });

            Wait('stop');
            $scope.parseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                variable: 'variables',
                parse_variable: 'parseType',
                field_id: 'inventory_variables'
            });
            LookUpInit({
                scope: $scope,
                form: form,
                current_item: $scope.organization,
                list: OrganizationList,
                field: 'organization',
                input_type: 'radio'
            });
            $scope.$emit('inventoryLoaded');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
        });
    // Save
    $scope.formSave = function () {
      Wait('start');

      // Make sure we have valid variable data
      json_data = ToJSON($scope.parseType, $scope.variables);

      data = {};
      for (fld in form.fields) {
          if (form.fields[fld].realName) {
              data[form.fields[fld].realName] = $scope[fld];
          } else {
              data[fld] = $scope[fld];
          }
      }

      Rest.setUrl(defaultUrl + inventory_id + '/');
      Rest.put(data)
          .success(function () {
              Wait('stop');
              $location.path('/inventories/');
          })
          .error(function (data, status) {
              ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                  msg: 'Failed to update inventory. PUT returned status: ' + status });
          });
    };

    $scope.manageInventory = function(){
      $location.path($location.path() + '/manage');
    };

    $scope.formCancel = function () {
        $state.transitionTo('inventories');
    };

    $scope.addScanJob = function(){
        $location.path($location.path()+'/job_templates/add');
    };

    $scope.launchScanJob = function(){
        PlaybookRun({ scope: $scope, id: this.scan_job_template.id });
    };

    $scope.scheduleScanJob = function(){
        $location.path('/job_templates/'+this.scan_job_template.id+'/schedules');
    };

    $scope.editScanJob = function(){
        $location.path($location.path()+'/job_templates/'+this.scan_job_template.id);
    };

    $scope.copyScanJobTemplate = function(){
      var  id = this.scan_job_template.id,
            name = this.scan_job_template.name,
            element,
            buttons = [{
              "label": "Cancel",
              "onClick": function() {
                  $(this).dialog('close');
              },
              "icon": "fa-times",
              "class": "btn btn-default",
              "id": "copy-close-button"
          },{
              "label": "Copy",
              "onClick": function() {
                  copyAction();
              },
              "icon":  "fa-copy",
              "class": "btn btn-primary",
              "id": "job-copy-button"
          }],
          copyAction = function () {
              // retrieve the copy of the job template object from the api, then overwrite the name and throw away the id
              Wait('start');
              var url = GetBasePath('job_templates')+id;
              Rest.setUrl(url);
              Rest.get()
                  .success(function (data) {
                      data.name = $scope.new_copy_name;
                      delete data.id;
                      $scope.$emit('GoToCopy', data);
                  })
                  .error(function (data) {
                      Wait('stop');
                      ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                          msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                  });
          };


      CreateDialog({
          id: 'copy-job-modal'    ,
          title: "Copy",
          scope: $scope,
          buttons: buttons,
          width: 500,
          height: 300,
          minWidth: 200,
          callback: 'CopyDialogReady'
      });

      $('#job_name').text(name);
      $('#copy-job-modal').show();


      if ($scope.removeCopyDialogReady) {
          $scope.removeCopyDialogReady();
      }
      $scope.removeCopyDialogReady = $scope.$on('CopyDialogReady', function() {
          //clear any old remaining text
          $scope.new_copy_name = "" ;
          $scope.copy_form.$setPristine();
          $('#copy-job-modal').dialog('open');
          $('#job-copy-button').attr('ng-disabled', "!copy_form.$valid");
          element = angular.element(document.getElementById('job-copy-button'));
          $compile(element)($scope);

      });

      if ($scope.removeGoToCopy) {
          $scope.removeGoToCopy();
      }
      $scope.removeGoToCopy = $scope.$on('GoToCopy', function(e, data) {
          var url = GetBasePath('job_templates'),
          old_survey_url = (data.related.survey_spec) ? data.related.survey_spec : "" ;
          Rest.setUrl(url);
          Rest.post(data)
              .success(function (data) {
                  if(data.survey_enabled===true){
                      $scope.$emit("CopySurvey", data, old_survey_url);
                  }
                  else {
                      $('#copy-job-modal').dialog('close');
                      Wait('stop');
                      $location.path($location.path() + '/job_templates/' + data.id);
                  }

              })
              .error(function (data) {
                  Wait('stop');
                  ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                      msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
              });
      });

      if ($scope.removeCopySurvey) {
          $scope.removeCopySurvey();
      }
      $scope.removeCopySurvey = $scope.$on('CopySurvey', function(e, new_data, old_url) {
          // var url = data.related.survey_spec;
          Rest.setUrl(old_url);
          Rest.get()
              .success(function (survey_data) {

                  Rest.setUrl(new_data.related.survey_spec);
                  Rest.post(survey_data)
                  .success(function () {
                      $('#copy-job-modal').dialog('close');
                      Wait('stop');
                      $location.path($location.path() + '/job_templates/' + new_data.id);
                  })
                  .error(function (data) {
                      Wait('stop');
                      ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                          msg: 'Call to ' + new_data.related.survey_spec + ' failed. DELETE returned status: ' + status });
                  });


              })
              .error(function (data) {
                  Wait('stop');
                  ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                      msg: 'Call to ' + old_url + ' failed. DELETE returned status: ' + status });
              });

      });

    };

    $scope.deleteScanJob = function () {
        var id = this.scan_job_template.id ,
          action = function () {
            $('#prompt-modal').modal('hide');
            Wait('start');
            deleteJobTemplate(id)
                .success(function () {
                  $('#prompt-modal').modal('hide');
                  $scope.search(form.related.scan_job_templates.iterator);
                })
                .error(function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the job template below?</div><div class="Prompt-bodyTarget">' + this.scan_job_template.name + '</div>',
            action: action,
            actionText: 'DELETE'
        });

    };

}

export default ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'InventoryForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'generateList',
    'OrganizationList', 'SearchInit', 'PaginateInit', 'LookUpInit',
    'GetBasePath', 'ParseTypeChange', 'Wait', 'ToJSON', 'ParseVariableString',
    'RelatedSearchInit', 'RelatedPaginateInit', 'Prompt',
    'PlaybookRun', 'CreateDialog', 'deleteJobTemplate', '$state',
    InventoriesEdit,
];
