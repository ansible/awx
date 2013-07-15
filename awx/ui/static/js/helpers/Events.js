/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  EventsHelper
 *
 *  EventView - show the job_events form in a modal dialog
 *
 */
angular.module('EventsHelper', ['RestServices', 'Utilities', 'JobEventFormDefinition'])
.factory('EventView', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobEventForm', 'GenerateForm', 
         'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, JobEventForm, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate) {
    return function(params) {
        var event_id = params.event_id;
        var generator = GenerateForm;
        var form = JobEventForm;
        var defaultUrl = GetBasePath('base') + 'job_events/' + event_id + '/';
        var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
        generator.reset();
        var master = {};
       
        scope.formModalAction = function() {
            $('#form-modal').modal("hide");
            }

        scope.formModalActionLabel = 'OK';
        //scope.formModalHeader = 'View Event';
        scope.formModalCancelShow = false;
        
        $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get()
            .success( function(data, status, headers, config) {
                for (var fld in form.fields) {
                    if (fld == 'status') {
                       if (data['failed']) {
                          scope['status'] = 'error';
                       }
                       else if (data['changed']) {
                          scope['status'] = 'changed';
                       }
                       else {
                          scope['status'] = 'success';
                       }
                    }
                    else if (fld == 'event_data') {
                       scope['event_data'] = JSON.stringify(data['event_data'], undefined, '\t');
                    }
                    else if (fld == 'host') {
                       if (data['summary_fields'] && data['summary_fields']['host']) {
                          scope['host'] = data['summary_fields']['host']['name'];
                       }
                    }
                    else {
                       if (fld == 'created') {
                          var cDate = new Date(data['created']);
                          scope['created'] = FormatDate(cDate);
                       }
                       else {
                          if (data[fld]) {
                             scope[fld] = data[fld];
                          }
                       }
                    }
                 }
                 
                 scope['formModalHeader'] = data.event_display.replace(/^\u00a0*/g,'');

                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve host: ' + event_id + '. GET status: ' + status });
                });
       
        if (!scope.$$phase) {
           scope.$digest();
        }
        
        }
        }]);