/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  EventsHelper
 *
 *  EventView - show the job_events form in a modal dialog
 *
 */
angular.module('EventsHelper', ['RestServices', 'Utilities'])
.factory('EventView', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 
         'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate) {
    return function(params) {
        
        // We're going to manipulate the form object each time user clicks on View button. We can't rely on what's
        // left of the form in memory each time. Instead we have to define the form from scratch, so for now we're
        // keeping it here inline rather than in a separate file.
        var form = {
            name: 'job_events',
            well: false,
            forceListeners: true,
            'class': 'horizontal-narrow',   
            fields: {
                status: {
                    labelClass: 'job-\{\{ status \}\}',
                    icon: 'icon-circle',
                    type: 'custom',
                    section: 'Event',
                    control: '<div class=\"job-event-status job-\{\{ status \}\}\">\{\{ status \}\}</div>'
                    },
                id: {
                    label: 'ID',
                    type: 'text',
                    readonly: true,
                    section: 'Event',
                    'class': 'span1'
                    },
                created: {
                    label: 'Created',
                    type: 'text',
                    section: 'Event',
                    readonly: true
                    },
                host: {
                    label: 'Host',
                    type: 'text',
                    readonly: true,
                    section: 'Event',
                    ngShow: "host !== ''"
                    },
                play: {
                    label: 'Play',
                    type: 'text',
                    readonly: true,
                    section: 'Event',
                    ngShow: "play !== ''"
                    },
                task: {
                    label: 'Task',
                    type: 'text',
                    readonly: true,
                    section: 'Event',
                    ngShow: "task !== ''"
                    },
                rc: {
                    label: 'Return Code',
                    type: 'text',
                    readonly: true,
                    section: 'Event',
                    'class': 'span1',
                    ngShow: "rc !== ''"
                    }, 
                msg: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                    section: 'Output',
                    'class': 'modal-input-xxlarge',
                    ngShow: "msg !== ''",
                    rows: 10
                    },
                stdout: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                    section: 'Output',
                    'class': 'modal-input-xxlarge',
                    ngShow: "stdout !== ''",
                    rows: 10
                    },
                stderr: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                    section: 'Output',
                    'class': 'modal-input-xxlarge',
                    ngShow: "stderr !== ''",
                    rows: 10
                    },
                results: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                     'class': 'modal-input-xxlarge',
                    ngShow: "results !== ''",
                    rows: 10
                    },
                start: {
                    label: 'Start',
                    type: 'text',
                    readonly: true, 
                    section: 'Timing',
                    ngShow: "start !== ''"
                    },
                traceback: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                    section: 'Traceback',
                    'class': 'modal-input-xxlarge',
                    ngShow: "traceback !== ''",
                    rows: 10
                    },
                end: {
                    label: 'End',
                    type: 'text',
                    readonly: true, 
                    section: 'Timing',
                    ngShow: "end !== ''"
                    },
                delta: {
                    label: 'Elapsed',
                    type: 'text',
                    readonly: true, 
                    section: 'Timing',
                    ngShow: "delta !== ''"
                    },
                module_name: {
                    label: 'Name',
                    type: 'text',
                    readonly: true,
                    section: 'Module',
                    ngShow: "module_name !== ''"
                    },
                module_args: {
                    label: 'Arguments',
                    type: 'text',
                    readonly: true,
                    section: 'Module',
                    ngShow: "module_args !== ''"
                    } 
                }
            };

        var event_id = params.event_id;
        var generator = GenerateForm;
        var scope;
        var defaultUrl = GetBasePath('base') + 'job_events/' + event_id + '/';
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get()
            .success( function(data, status, headers, config) {
                
                // If event_data is not available or not very useful
                if ($.isEmptyObject(data['event_data']) || !data['event_data']['res'] || typeof data['event_data']['res'] == 'string') {
                   for (var fld in form.fields) {
                       switch(fld) {
                           case 'start':
                           case 'end':
                           case 'delta':
                           case 'msg':
                           case 'stdout':
                           case 'stderr':
                           case 'msg':
                           case 'results':
                           case 'module_name': 
                           case 'module_args':
                           delete form.fields[fld];
                           break;
                       }
                   }
                }
                else if (typeof data['event_data']['res'] != 'string') {
                   delete form.fields['traceback'];
                }
                
                // Remove remaining form fields that do not have a corresponding data value
                for (var fld in form.fields) {
                    switch (fld) {
                        case 'start':
                        case 'end':
                        case 'delta':
                        case 'msg':
                        case 'stdout':
                        case 'stderr':
                        case 'msg':
                            if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] == undefined) {
                               delete form.fields[fld];
                            }
                            else {
                               if (form.fields[fld].type == 'textarea') {
                                  var n = data['event_data']['res'][fld].match(/\n/g);
                                  var rows = (n) ? n.length : 1;
                                  rows = (rows > 10) ? 10 : rows;
                                  rows = (rows < 3) ? 3 : rows;
                                  form.fields[fld].rows = rows;
                               }
                            }
                            break;
                        case 'results':
                            if ( data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] == undefined) {
                               // not defined
                               delete form.fields[fld];
                            }
                            else if (!Array.isArray(data['event_data']['res'][fld]) || data['event_data']['res'][fld].length == 0) {
                               // defined, but empty
                               delete form.fields[fld];
                            }
                            else {
                               // defined and not empty, so attempt to size the textarea field
                               var txt = '';
                               for (var i=0; i < data['event_data']['res'][fld].length; i++) {
                                   txt += data['event_data']['res'][fld][i];
                               }
                               if (txt == '') {
                                  // there's an array, but the actual text is empty
                                  delete form.fields[fld];
                               }
                               else {
                                 var n = txt.match(/\n/g);
                                 var rows = (n) ? n.length : 1;
                                 rows = (rows > 10) ? 10 : rows;
                                 rows = (rows < 3) ? 3 : rows;
                                 form.fields[fld].rows = rows;
                               }
                            }
                            break;
                        case 'module_name':
                        case 'module_args':
                            if (data['event_data'] && data['event_data']['res']) {
                                if (data['event_data']['res']['invocation'] === undefined ||
                                    data['event_data']['res']['invocation'][fld] === undefined) {
                                    delete form.fields[fld];
                                }
                            }
                            break;
                    }
                }

                // load up the form
                scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
                generator.reset();
                scope.formModalAction = function() {
                    $('#form-modal').modal("hide");
                    }
                scope.formModalActionLabel = 'OK';
                scope.formModalCancelShow = false;
                $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
                $('#form-modal').addClass('skinny-modal');

                scope.formModalHeader = data['event_display'].replace(/^\u00a0*/g,'');
                
                if (typeof data['event_data']['res'] == 'string') {
                   scope['traceback'] = data['event_data']['res'];
                }

                //scope.event_data = JSON.stringify(data['event_data'], null, '\t');
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
                        case 'play':
                            scope[fld] = data[fld];
                            break;
                        case 'start':
                        case 'end':
                            if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] !== undefined) {
                               var cDate = new Date(data['event_data']['res'][fld]);
                               scope[fld] = FormatDate(cDate);
                            }
                            break;
                        case 'results': 
                            if (Array.isArray(data['event_data']['res'][fld]) && data['event_data']['res'][fld].length > 0 ) {
                               var txt = '';
                               for (var i=0; i < data['event_data']['res'][fld].length; i++) {
                                   txt += data['event_data']['res'][fld][i];
                               }
                               if (txt !== '') {
                                  scope[fld] = txt;
                               }
                            }
                            break; 
                        case 'msg':
                        case 'stdout':
                        case 'stderr':
                        case 'delta':
                        case 'rc':
                            if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] !== undefined) {
                               scope[fld] = data['event_data']['res'][fld];
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
                
                if (!scope.$$phase) {
                    scope.$digest();
                }

                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve event: ' + event_id + '. GET status: ' + status });
                });
        
        }
        }]);