/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Schedules Helper
 *
 *  Display the scheduler widget in a dialog
 *
 */

'use strict';

angular.module('SchedulesHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'ModalDialog' ])
  
    .factory('ShowSchedulerModal', ['Wait', 'CreateDialog', function(Wait, CreateDialog) {
        return function(params) {
            // Set modal dimensions based on viewport width
            
            var buttons,
                scope = params.scope,
                callback = params.callback;

            buttons = [{
                "label": "Cancel",
                "onClick": function() {
                    $(this).dialog('close');
                },
                "icon": "fa-times",
                "class": "btn btn-default",
                "id": "schedule-close-button"
            },{
                "label": "Save",
                "onClick": function() {
                    setTimeout(function(){
                        scope.$apply(function(){
                            scope.saveSchedule();
                        });
                    });
                },
                "icon": "fa-check",
                "class": "btn btn-primary",
                "id": "schedule-save-button"
            }];

            CreateDialog({
                id: 'scheduler-modal-dialog',
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 725,
                minWidth: 400,
                onClose: function() {
                    $('#scheduler-modal-dialog #form-container').empty();
                },
                onOpen: function() {
                    Wait('stop');
                    $('#scheduler-tabs a:first').tab('show');
                    $('#schedulerName').focus();
                    $('#rrule_nlp_description').dblclick(function() {
                        setTimeout(function() { scope.$apply(function() { scope.showRRule = (scope.showRRule) ? false : true; }); }, 100);
                    });
                },
                callback: callback
            });
        };
    }])

    .factory('EditSchedule', ['SchedulerInit', 'ShowSchedulerModal', 'Wait', 'Rest', 'ProcessErrors', 'GetBasePath', 'SchedulePost',
    function(SchedulerInit, ShowSchedulerModal, Wait, Rest, ProcessErrors, GetBasePath, SchedulePost) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                callback = params.callback,
                schedule, scheduler,
                url = GetBasePath('schedules') + id + '/';
                
            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#scheduler-modal-dialog').dialog('open');
                $('#schedulerName').focus();
                setTimeout(function() {
                    scope.$apply(function() {
                        scheduler.setRRule(schedule.rrule);
                        scheduler.setName(schedule.name);
                    });
                }, 300);
            });

            if (scope.removeScheduleFound) {
                scope.removeScheduleFound();
            }
            scope.removeScheduleFound = scope.$on('ScheduleFound', function() {
                $('#form-container').empty();
                scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
                scheduler.inject('form-container', false);
                scheduler.injectDetail('occurrences', false);

                if (!/DTSTART/.test(schedule.rrule)) {
                    schedule.rrule += ";DTSTART=" + schedule.dtstart.replace(/\.\d+Z$/,'Z');
                }
                schedule.rrule = schedule.rrule.replace(/ RRULE:/,';');
                schedule.rrule = schedule.rrule.replace(/DTSTART:/,'DTSTART=');

                ShowSchedulerModal({ scope: scope, callback: 'DialogReady' });
                scope.showRRuleDetail = false;
            });


            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
                Wait('stop');
                $('#scheduler-modal-dialog').dialog('close');
                if (callback) {
                    scope.$emit(callback);
                }
            });

            scope.saveSchedule = function() {
                $('#scheduler-tabs a:first').tab('show');
                SchedulePost({
                    scope: scope,
                    url: url,
                    scheduler: scheduler,
                    callback: 'ScheduleSaved',
                    mode: 'edit',
                    schedule: schedule
                });
            };

            $('#scheduler-tabs li a').on('shown.bs.tab', function(e) {
                if ($(e.target).text() === 'Details') {
                    if (!scheduler.isValid()) {
                        $('#scheduler-tabs a:first').tab('show');
                    }
                }
            });

            Wait('start');

            // Get the existing record
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    schedule = data;
                    scope.$emit('ScheduleFound');
                })
                .error(function(data,status){
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                });
        };
    }])

    .factory('AddSchedule', ['$location', '$routeParams', 'SchedulerInit', 'ShowSchedulerModal', 'Wait', 'GetBasePath', 'Empty',
        'SchedulePost',
    function($location, $routeParams, SchedulerInit, ShowSchedulerModal, Wait, GetBasePath, Empty, SchedulePost) {
        return function(params) {
            var scope = params.scope,
                callback= params.callback,
                base = $location.path().replace(/^\//, '').split('/')[0],
                url =  GetBasePath(base),
                scheduler;

            url += (!Empty($routeParams.id)) ? $routeParams.id + '/schedules/' : '';

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#scheduler-modal-dialog').dialog('open');
                $('#schedulerName').focus();
            });

            Wait('start');
            $('#form-container').empty();
            scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
            scheduler.inject('form-container', false);
            scheduler.injectDetail('occurrences', false);
            scheduler.clear();
            ShowSchedulerModal({ scope: scope, callback: 'DialogReady' });
            scope.showRRuleDetail = false;

            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
                Wait('stop');
                $('#scheduler-modal-dialog').dialog('close');
                if (callback) {
                    scope.$emit(callback);
                }
            });

            scope.saveSchedule = function() {
                $('#scheduler-tabs a:first').tab('show');
                SchedulePost({
                    scope: scope,
                    url: url,
                    scheduler: scheduler,
                    callback: 'ScheduleSaved',
                    mode: 'add'
                });
            };

            $('#scheduler-tabs li a').on('shown.bs.tab', function(e) {
                if ($(e.target).text() === 'Details') {
                    if (!scheduler.isValid()) {
                        $('#scheduler-tabs a:first').tab('show');
                    }
                }
            });
        };
    }])

    .factory('SchedulePost', ['Rest', 'ProcessErrors', 'RRuleToAPI', 'Wait', function(Rest, ProcessErrors, RRuleToAPI, Wait) {
        return function(params) {
            var scope = params.scope,
                url = params.url,
                scheduler = params.scheduler,
                mode = params.mode,
                schedule = (params.schedule) ? params.schedule : {},
                callback = params.callback,
                newSchedule, rrule;
                
            if (scheduler.isValid()) {
                Wait('start');
                newSchedule = scheduler.getValue();
                rrule = scheduler.getRRule();
                schedule.name = newSchedule.name;
                schedule.rrule = RRuleToAPI(rrule.toString());
                schedule.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();
                Rest.setUrl(url);
                if (mode === 'add') {
                    Rest.post(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
                else {
                    Rest.put(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
            }
            else {
                return false;
            }
        };
    }])

    /**
     * Inject the scheduler_dialog.html wherever needed 
     */
    .factory('LoadDialogPartial', ['Rest', '$compile', 'ProcessErrors', function(Rest, $compile, ProcessErrors) {
        return function(params) {
            
            var scope = params.scope,
                element_id = params.element_id,
                callback = params.callback,
                url;

            // Add the schedule_dialog.html partial 
            url = '/static/partials/schedule_dialog.html';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    var e = angular.element(document.getElementById(element_id));
                    e.append(data);
                    $compile(e)(scope);
                    scope.$emit(callback);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. GET returned: ' + status });
                });
        };
    }])

    /**
     * Flip a schedule's enable flag
     *
     * ToggleSchedule({
     *     scope:       scope,
     *     id:          schedule.id to update
     *     callback:    scope.$emit label to call when update completes
     * });
     *
     */
    .factory('ToggleSchedule', ['Wait', 'GetBasePath', 'ProcessErrors', 'Rest', function(Wait, GetBasePath, ProcessErrors, Rest) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                callback = params.callback,
                url = GetBasePath('schedules') + id +'/';
            
            // Perform the update
            if (scope.removeScheduleFound) {
                scope.removeScheduleFound();
            }
            scope.removeScheduleFound = scope.$on('ScheduleFound', function(e, data) {
                data.enabled = (data.enabled) ? false : true;
                Rest.put(data)
                    .success( function() {
                        if (callback) {
                            scope.$emit(callback, id);
                        }
                        else {
                            Wait('stop');
                        }
                    })
                    .error( function() {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update schedule ' + id + ' PUT returned: ' + status });
                    });
            });

            Wait('start');

            // Get the schedule
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.$emit('ScheduleFound', data);
                })
                .error(function(data,status){
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                });
        };
    }])

    /**
     * Delete a schedule. Prompts user to confirm delete
     *
     * DeleteSchedule({
     *     scope:       $scope containing list of schedules
     *     id:          id of schedule to delete
     *     callback:    $scope.$emit label to call when delete is completed
     * })
     *
     */
    .factory('DeleteSchedule', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', 'Prompt', 'Find',
    function(GetBasePath, Rest, Wait, ProcessErrors, Prompt, Find) {
        return function(params) {

            var scope = params.scope,
                id = params.id,
                callback = params.callback,
                action, schedule, list, url, hdr;

            if (scope.schedules) {
                list = scope.schedules;
            }
            else if (scope.scheduled_jobs) {
                list = scope.scheduled_jobs;
            }

            url = GetBasePath('schedules') + id + '/';
            schedule = Find({list: list, key: 'id', val: id });
            hdr = 'Delete Schedule';

            action = function () {
                Wait('start');
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        scope.$emit(callback, id);
                    })
                    .error(function (data, status) {
                        try {
                            $('#prompt-modal').modal('hide');
                        }
                        catch(e) {
                            // ignore
                        }
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            ' failed. DELETE returned: ' + status });
                    });
            };

            Prompt({
                hdr: hdr,
                body: "<div class=\"alert alert-info\">Are you sure you want to delete the <em>" + schedule.name  + "</em> schedule?</div>",
                action: action
            });

        };
    }])

    /**
     * Convert rrule string to an API agreeable format
     *
     */
    .factory('RRuleToAPI', [ function() {
        return function(rrule) {
            var response;
            response = rrule.replace(/(^.*(?=DTSTART))(DTSTART=.*?;)(.*$)/, function(str, p1, p2, p3) {
                return p2.replace(/\;/,'').replace(/=/,':') + ' ' + 'RRULE:' + p1 + p3;
            });
            return response;
        };
    }])


    .factory('SchedulesControllerInit', ['$location', 'ToggleSchedule', 'DeleteSchedule', 'EditSchedule', 'AddSchedule',
        function($location, ToggleSchedule, DeleteSchedule, EditSchedule, AddSchedule) {
        return function(params) {
            var scope = params.scope,
                parent_scope = params.parent_scope,
                iterator = (params.iterator) ? params.iterator : scope.iterator,
                base = $location.path().replace(/^\//, '').split('/')[0];

            scope.toggleSchedule = function(event, id) {
                try {
                    $(event.target).tooltip('hide');
                }
                catch(e) {
                    // ignore
                }
                ToggleSchedule({
                    scope: scope,
                    id: id,
                    callback: 'SchedulesRefresh'
                });
            };

            scope.deleteSchedule = function(id) {
                DeleteSchedule({
                    scope: scope,
                    id: id,
                    callback: 'SchedulesRefresh'
                });
            };

            scope.editSchedule = function(id) {
                EditSchedule({
                    scope: scope,
                    id: id,
                    callback: 'SchedulesRefresh'
                });
            };

            scope.addSchedule = function() {
                AddSchedule({
                    scope: scope,
                    callback: 'SchedulesRefresh'
                });
            };

            scope.refreshSchedules = function() {
                if (base === 'jobs') {
                    parent_scope.refreshJobs();
                }
                else {
                    scope.search(iterator);
                }
            };

            if (scope.removeSchedulesRefresh) {
                scope.removeSchedulesRefresh();
            }
            scope.$on('SchedulesRefresh', function() {
                scope.search(iterator);
            });
        };
    }])

    .factory('SchedulesListInit', [ function() {
        return function(params) {
            var scope = params.scope,
                list = params.list,
                choices = params.choices;
            scope[list.name].forEach(function(item, item_idx) {
                var fld, field,
                    itm = scope[list.name][item_idx];
                itm.enabled = (itm.enabled) ? true : false;
                if (itm.enabled) {
                    itm.play_tip = 'Schedule is active. Click to stop.';
                    itm.status = 'active';
                    itm.status_tip = 'Schedule is active. Click to stop.';
                }
                else {
                    itm.play_tip = 'Schedule is stopped. Click to activate.';
                    itm.status = 'stopped';
                    itm.status_tip = 'Schedule is stopped. Click to activate.';
                }
                itm.nameTip = item.name + " schedule. Click to edit.";
                // Copy summary_field values
                for (field in list.fields) {
                    fld = list.fields[field];
                    if (fld.sourceModel) {
                        if (itm.summary_fields[fld.sourceModel]) {
                            itm[field] = itm.summary_fields[fld.sourceModel][fld.sourceField];
                        }
                    }
                }
                // Set the item type label
                if (list.fields.type) {
                    choices.every(function(choice) {
                        if (choice.value === item.type) {
                            itm.type_label = choice.label;
                            return false;
                        }
                        return true;
                    });
                }
            });
        };
    }])

    /**
     * 
     *  Called from a controller to setup the scope for a schedules list
     *
     */
    .factory('LoadSchedulesScope', ['SearchInit', 'PaginateInit', 'GenerateList', 'SchedulesControllerInit', 'SchedulesListInit',
        function(SearchInit, PaginateInit, GenerateList, SchedulesControllerInit, SchedulesListInit) {
        return function(params) {
            var parent_scope = params.parent_scope,
                scope = params.scope,
                list = params.list,
                id = params.id,
                url = params.url,
                pageSize = params.pageSize || 5;

            GenerateList.inject(list, {
                mode: 'edit',
                id: id,
                breadCrumbs: false,
                scope: scope,
                searchSize: 'col-lg-4 col-md-6 col-sm-12 col-xs-12',
                showSearch: true
            });

            SearchInit({
                scope: scope,
                set: list.name,
                list: list,
                url: url
            });

            PaginateInit({
                scope: scope,
                list: list,
                url: url,
                pageSize: pageSize
            });

            scope.iterator = list.iterator;

            if (scope.removePostRefresh) {
                scope.removePostRefresh();
            }
            scope.$on('PostRefresh', function(){
                SchedulesControllerInit({
                    scope: scope,
                    parent_scope: parent_scope,
                    list: list
                });
                SchedulesListInit({
                    scope: scope,
                    list: list,
                    choices: parent_scope.type_choices
                });
                parent_scope.$emit('listLoaded');
            });
            scope.search(list.iterator);
        };
    }]);


































































