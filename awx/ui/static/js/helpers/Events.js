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
                    switch(fld) {
                        case 'status':
                           if (data['failed']) {
                              scope['status'] = 'error';
                           }
                           else if (data['changed']) {
                              scope['status'] = 'changed';
                           }
                           else {
                              scope['status'] = 'success';
                           }
                           break;
                        case 'created':
                           var cDate = new Date(data['created']);
                           scope['created'] = FormatDate(cDate);
                           break;
                        case 'host':
                           if (data['summary_fields'] && data['summary_fields']['host']) {
                              scope['host'] = data['summary_fields']['host']['name'];
                           }
                           break;
                        case 'id':
                        case 'task':
                           scope[fld] = data[fld];
                           break;
                        case 'msg':
                        case 'stdout':
                        case 'stderr':
                        case 'start':
                        case 'end':
                        case 'delta':
                        case 'rc':
                           if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] !== undefined) {
                              scope[fld] = data['event_data']['res'][fld];
                              if (form.fields[fld].type == 'textarea') {
                                 var n = data['event_data']['res'][fld].match(/\n/g);
                                 rows = (n) ? n.length : 1;
                                 rows = (rows > 5) ? 5 : rows;
                                 $('textarea[name="' + fld + '"]').attr('rows',rows);
                              }
                            }
                           break;
                        case 'conditional':
                           if (data['event_data']['res']) {
                              scope[fld] = data['event_data']['res']['is_conditional'];
                           }
                           break;
                        case 'module_name':
                        case 'module_args':
                           if (data['event_data']['res'] && data['event_data']['res']['invocation']) {
                              scope[fld] = data['event_data']['res']['invocation'][fld];
                           }
                           break;
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