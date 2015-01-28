/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  EventsHelper
 *
 *
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:Events
 * @description    EventView - show the job_events form in a modal dialog
*/


angular.module('EventsHelper', ['RestServices', 'Utilities', 'JobEventDataDefinition', 'JobEventsFormDefinition'])

    .factory('EventView', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm',
        'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'JobEventDataForm', 'Empty', 'JobEventsForm',
        function ($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
        FormatDate, JobEventDataForm, Empty, JobEventsForm) {
        return function (params) {

            var event_id = params.event_id,
                generator = GenerateForm,
                form = angular.copy(JobEventsForm),
                scope,
                defaultUrl = GetBasePath('base') + 'job_events/' + event_id + '/';

            // Retrieve detail record and prepopulate the form
            Rest.setUrl(defaultUrl);
            Rest.get()
                .success(function (data) {
                    var i, n, fld, rows, txt, cDate;

                    // If event_data is not available, remove fields that depend on it
                    if ($.isEmptyObject(data.event_data) || !data.event_data.res || typeof data.event_data.res === 'string') {
                        for (fld in form.fields) {
                            switch (fld) {
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
                            case 'rc':
                                delete form.fields[fld];
                                break;
                            }
                        }
                    }

                    if ($.isEmptyObject(data.event_data) || !data.event_data.res || typeof data.event_data.res !== 'string') {
                        delete form.fields.traceback;
                    }

                    // Remove remaining form fields that do not have a corresponding data value
                    for (fld in form.fields) {
                        switch (fld) {
                        case 'start':
                        case 'end':
                        case 'delta':
                        case 'msg':
                        case 'stdout':
                        case 'stderr':
                        case 'msg':
                        case 'rc':
                            if (data.event_data && data.event_data.res && Empty(data.event_data.res[fld])) {
                                delete form.fields[fld];
                            } else {
                                if (form.fields[fld].type === 'textarea') {
                                    n = data.event_data.res[fld].match(/\n/g);
                                    rows = (n) ? n.length : 1;
                                    rows = (rows > 10) ? 10 : rows;
                                    rows = (rows < 3) ? 3 : rows;
                                    form.fields[fld].rows = rows;
                                }
                            }
                            break;
                        case 'results':
                            if (data.event_data && data.event_data.res && data.event_data.res[fld] === undefined) {
                                // not defined
                                delete form.fields[fld];
                            } else if (!Array.isArray(data.event_data.res[fld]) || data.event_data.res[fld].length === 0) {
                                // defined, but empty
                                delete form.fields[fld];
                            } else {
                                // defined and not empty, so attempt to size the textarea field
                                txt = '';
                                for (i = 0; i < data.event_data.res[fld].length; i++) {
                                    txt += data.event_data.res[fld][i];
                                }
                                if (txt === '') {
                                    // there's an array, but the actual text is empty
                                    delete form.fields[fld];
                                } else {
                                    n = txt.match(/\n/g);
                                    rows = (n) ? n.length : 1;
                                    rows = (rows > 10) ? 10 : rows;
                                    rows = (rows < 3) ? 3 : rows;
                                    form.fields[fld].rows = rows;
                                }
                            }
                            break;
                        case 'module_name':
                        case 'module_args':
                            if (data.event_data && data.event_data.res) {
                                if (data.event_data.res.invocation === undefined ||
                                    data.event_data.res.invocation[fld] === undefined) {
                                    delete form.fields[fld];
                                }
                            }
                            break;
                        }
                    }

                    // load the form
                    scope = generator.inject(form, {
                        mode: 'edit',
                        modal: true,
                        related: false
                    });
                    generator.reset();
                    scope.formModalAction = function () {
                        $('#form-modal').modal("hide");
                    };
                    scope.formModalActionLabel = 'OK';
                    scope.formModalCancelShow = false;
                    scope.formModalInfo = 'View JSON';
                    $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
                    $('#form-modal').addClass('skinny-modal');
                    scope.formModalHeader = data.event_display.replace(/^\u00a0*/g, '');

                    // Respond to View JSON button
                    scope.formModalInfoAction = function () {
                        var generator = GenerateForm,
                        scope = generator.inject(JobEventDataForm, {
                            mode: 'edit',
                            modal: true,
                            related: false,
                            modal_selector: '#form-modal2',
                            modal_body_id: 'form-modal2-body',
                            modal_title_id: 'formModal2Header'
                        });
                        generator.reset();
                        scope.formModal2Header = data.event_display.replace(/^\u00a0*/g, '');
                        scope.event_data = JSON.stringify(data.event_data, null, '\t');
                        scope.formModal2ActionLabel = 'OK';
                        scope.formModal2CancelShow = false;
                        scope.formModal2Info = false;
                        scope.formModalInfo = 'View JSON';
                        scope.formModal2Action = function () {
                            $('#form-modal2').modal("hide");
                        };
                        $('#form-modal2 .btn-success').removeClass('btn-success').addClass('btn-none');
                    };

                    if (typeof data.event_data.res === 'string') {
                        scope.traceback = data.event_data.res;
                    }

                    for (fld in form.fields) {
                        switch (fld) {
                        case 'status':
                            if (data.failed) {
                                scope.status = 'error';
                            } else if (data.changed) {
                                scope.status = 'changed';
                            } else {
                                scope.status = 'success';
                            }
                            break;
                        case 'created':
                            cDate = new Date(data.created);
                            scope.created = FormatDate(cDate);
                            break;
                        case 'host':
                            if (data.summary_fields && data.summary_fields.host) {
                                scope.host = data.summary_fields.host.name;
                            }
                            break;
                        case 'id':
                        case 'task':
                        case 'play':
                            scope[fld] = data[fld];
                            break;
                        case 'start':
                        case 'end':
                            if (data.event_data && data.event_data.res && !Empty(data.event_data.res[fld])) {
                                scope[fld] = data.event_data.res[fld];
                            }

                            break;
                        case 'results':
                            if (Array.isArray(data.event_data.res[fld]) && data.event_data.res[fld].length > 0) {
                                txt = '';
                                for (i = 0; i < data.event_data.res[fld].length; i++) {
                                    txt += data.event_data.res[fld][i];
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
                            if (data.event_data && data.event_data.res && data.event_data.res[fld] !== undefined) {
                                scope[fld] = data.event_data.res[fld];
                            }
                            break;
                        case 'module_name':
                        case 'module_args':
                            if (data.event_data.res && data.event_data.res.invocation) {
                                scope[fld] = data.event_data.res.invocation[fld];
                            }
                            break;
                        }
                    }

                    if (!scope.$$phase) {
                        scope.$digest();
                    }

                })
                .error(function (data, status) {
                    $('#form-modal').modal("hide");
                    ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to retrieve event: ' + event_id + '. GET status: ' + status });
                });
        };
    }
    ]);