/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

    /**
 * @ngdoc function
 * @name helpers.function:Schedules
 * @description
 *  Schedules Helper
 *
 *  Display the scheduler widget in a dialog
 *
 */

import listGenerator from '../shared/list-generator/main';

export default
    angular.module('SchedulesHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', listGenerator.name, 'ModalDialog',
        'GeneratorHelpers'])

        .factory('EditSchedule', ['SchedulerInit', '$rootScope', 'Wait', 'Rest',
        'ProcessErrors', 'GetBasePath', 'SchedulePost', '$state',
        function(SchedulerInit, $rootScope, Wait, Rest, ProcessErrors,
            GetBasePath, SchedulePost, $state) {
            return function(params) {
                var scope = params.scope,
                    id = params.id,
                    callback = params.callback,
                    schedule, scheduler,
                    url = GetBasePath('schedules') + id + '/';

                delete scope.isFactCleanup;
                delete scope.cleanupJob;

                function setGranularity(){
                    var a,b, prompt_for_days,
                        keep_unit,
                        granularity,
                        granularity_keep_unit;

                    if(scope.cleanupJob){
                        scope.schedulerPurgeDays = Number(schedule.extra_data.days);
                        // scope.scheduler_form.schedulerPurgeDays.$setViewValue( Number(schedule.extra_data.days));
                    }
                    else if(scope.isFactCleanup){
                        scope.keep_unit_choices = [{
                            "label" : "Days",
                            "value" : "d"
                        },
                        {
                            "label": "Weeks",
                            "value" : "w"
                        },
                        {
                            "label" : "Years",
                            "value" : "y"
                        }];
                        scope.granularity_keep_unit_choices =  [{
                            "label" : "Days",
                            "value" : "d"
                        },
                        {
                            "label": "Weeks",
                            "value" : "w"
                        },
                        {
                            "label" : "Years",
                            "value" : "y"
                        }];
                        // the API returns something like 20w or 1y
                        a = schedule.extra_data.older_than; // "20y"
                        b = schedule.extra_data.granularity; // "1w"
                        prompt_for_days = Number(_.initial(a,1).join('')); // 20
                        keep_unit = _.last(a); // "y"
                        granularity = Number(_.initial(b,1).join('')); // 1
                        granularity_keep_unit = _.last(b); // "w"

                        scope.keep_amount = prompt_for_days;
                        scope.granularity_keep_amount = granularity;
                        scope.keep_unit = _.find(scope.keep_unit_choices, function(i){
                            return i.value === keep_unit;
                        });
                        scope.granularity_keep_unit =_.find(scope.granularity_keep_unit_choices, function(i){
                            return i.value === granularity_keep_unit;
                        });
                    }
                }

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
                    scope.$on("htmlDetailReady", function() {
                        scheduler.setRRule(schedule.rrule);
                        scheduler.setName(schedule.name);
                        $rootScope.$broadcast("ScheduleFormCreated", scope);
                    });
                    scope.showRRuleDetail = false;

                    scheduler.setRRule(schedule.rrule);
                    scheduler.setName(schedule.name);
                    if(scope.isFactCleanup || scope.cleanupJob){
                        setGranularity();
                    }
                });


                if (scope.removeScheduleSaved) {
                    scope.removeScheduleSaved();
                }
                scope.removeScheduleSaved = scope.$on('ScheduleSaved', function(e, data) {
                    Wait('stop');
                    if (callback) {
                        scope.$emit(callback, data);
                    }
                    $state.go("^");
                });
                scope.saveSchedule = function() {
                    schedule.extra_data = scope.extraVars;
                    SchedulePost({
                        scope: scope,
                        url: url,
                        scheduler: scheduler,
                        callback: 'ScheduleSaved',
                        mode: 'edit',
                        schedule: schedule
                    });
                };

                Wait('start');

                // Get the existing record
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        schedule = data;
                        scope.extraVars = data.extra_data === '' ? '---' : '---\n' + jsyaml.safeDump(data.extra_data);

                        if(schedule.extra_data.hasOwnProperty('granularity')){
                            scope.isFactCleanup = true;
                        }
                        if (schedule.extra_data.hasOwnProperty('days')){
                            scope.cleanupJob = true;
                        }

                        scope.schedule_obj = data;

                        scope.$emit('ScheduleFound');
                    })
                    .error(function(data,status){
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                    });
            };
        }])

        .factory('AddSchedule', ['$location', '$rootScope', '$stateParams',
        'SchedulerInit', 'Wait', 'GetBasePath', 'Empty', 'SchedulePost', '$state', 'Rest', 'ProcessErrors',
        function($location, $rootScope, $stateParams, SchedulerInit,
            Wait, GetBasePath, Empty, SchedulePost, $state, Rest,
            ProcessErrors) {
            return function(params) {
                var scope = params.scope,
                    callback= params.callback,
                    base = params.base || $location.path().replace(/^\//, '').split('/')[0],
                    url = params.url || null,
                    scheduler;

                if (!Empty($stateParams.id) && base !== 'system_job_templates' && base !== 'inventories') {
                    url = GetBasePath(base) + $stateParams.id + '/schedules/';
                }
                else if(base === "inventories"){
                    if (!params.url){
                        url = GetBasePath('groups') + $stateParams.id + '/';
                        Rest.setUrl(url);
                        Rest.get().
                        then(function (data) {
                                url = data.data.related.inventory_source + 'schedules/';
                            }).catch(function (response) {
                            ProcessErrors(null, response.data, response.status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get inventory group info. GET returned status: ' +
                                response.status
                            });
                        });
                    }
                    else {
                        url = params.url;
                    }
                }
                else if (base === 'system_job_templates') {
                    url = GetBasePath(base) + $stateParams.id + '/schedules/';
                    if($stateParams.id  === 4){
                        scope.isFactCleanup = true;
                        scope.keep_unit_choices = [{
                            "label" : "Days",
                            "value" : "d"
                        },
                        {
                            "label": "Weeks",
                            "value" : "w"
                        },
                        {
                            "label" : "Years",
                            "value" : "y"
                        }];
                        scope.granularity_keep_unit_choices =  [{
                            "label" : "Days",
                            "value" : "d"
                        },
                        {
                            "label": "Weeks",
                            "value" : "w"
                        },
                        {
                            "label" : "Years",
                            "value" : "y"
                        }];
                        scope.prompt_for_days_facts_form.keep_amount.$setViewValue(30);
                        scope.prompt_for_days_facts_form.granularity_keep_amount.$setViewValue(1);
                        scope.keep_unit = scope.keep_unit_choices[0];
                        scope.granularity_keep_unit = scope.granularity_keep_unit_choices[1];
                    }
                    else {
                        scope.cleanupJob = true;
                    }
                }

                Wait('start');
                $('#form-container').empty();
                scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
                if(scope.schedulerUTCTime) {
                    // The UTC time is already set
                    scope.processSchedulerEndDt();
                }
                else {
                    // We need to wait for it to be set by angular-scheduler because the following function depends
                    // on it
                    var schedulerUTCTimeWatcher = scope.$watch('schedulerUTCTime', function(newVal) {
                        if(newVal) {
                            // Remove the watcher
                            schedulerUTCTimeWatcher();
                            scope.processSchedulerEndDt();
                        }
                    });
                }
                scheduler.inject('form-container', false);
                scheduler.injectDetail('occurrences', false);
                scheduler.clear();
                scope.$on("htmlDetailReady", function() {
                    $rootScope.$broadcast("ScheduleFormCreated", scope);
                });
                scope.showRRuleDetail = false;

                if (scope.removeScheduleSaved) {
                    scope.removeScheduleSaved();
                }
                scope.removeScheduleSaved = scope.$on('ScheduleSaved', function(e, data) {
                    Wait('stop');
                    if (callback) {
                        scope.$emit(callback, data);
                    }
                    $state.go("^", null, {reload: true});
                });
                scope.saveSchedule = function() {
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

        .factory('SchedulePost', ['Rest', 'ProcessErrors', 'RRuleToAPI', 'Wait',
            function(Rest, ProcessErrors, RRuleToAPI, Wait) {
            return function(params) {
                var scope = params.scope,
                    url = params.url,
                    scheduler = params.scheduler,
                    mode = params.mode,
                    schedule = (params.schedule) ? params.schedule : {},
                    callback = params.callback,
                    newSchedule, rrule, extra_vars;
                if (scheduler.isValid()) {
                    Wait('start');
                    newSchedule = scheduler.getValue();
                    rrule = scheduler.getRRule();
                    schedule.name = newSchedule.name;
                    schedule.rrule = RRuleToAPI(rrule.toString());
                    schedule.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();

                    if (scope.isFactCleanup) {
                        extra_vars = {
                            "older_than": scope.scheduler_form.keep_amount.$viewValue + scope.scheduler_form.keep_unit.$viewValue.value,
                            "granularity": scope.scheduler_form.granularity_keep_amount.$viewValue + scope.scheduler_form.granularity_keep_unit.$viewValue.value
                        };
                        schedule.extra_data = JSON.stringify(extra_vars);
                    } else if (scope.cleanupJob) {
                        extra_vars = {
                            "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                        };
                        schedule.extra_data = JSON.stringify(extra_vars);
                    }
                    else if(scope.extraVars){
                        schedule.extra_data = scope.parseType === 'yaml' ?
                            (scope.extraVars === '---' ? "" : jsyaml.safeLoad(scope.extraVars)) : scope.extraVars;
                    }
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
                                    scope.$emit(callback, schedule);
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
         * Flip a schedule's enable flag
         *
         * ToggleSchedule({
         *     scope:       scope,
         *     id:          schedule.id to update
         *     callback:    scope.$emit label to call when update completes
         * });
         *
         */
        .factory('ToggleSchedule', ['Wait', 'GetBasePath', 'ProcessErrors', 'Rest', '$state',
            function(Wait, GetBasePath, ProcessErrors, Rest, $state) {
            return function(params) {
                var scope = params.scope,
                    id = params.id,
                    url = GetBasePath('schedules') + id +'/';

                // Perform the update
                if (scope.removeScheduleFound) {
                    scope.removeScheduleFound();
                }
                scope.removeScheduleFound = scope.$on('ScheduleFound', function(e, data) {
                    data.enabled = (data.enabled) ? false : true;
                    Rest.put(data)
                        .success( function() {
                            Wait('stop');
                            $state.go('.', null, {reload: true});
                        })
                        .error( function(data, status) {
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
        .factory('DeleteSchedule', ['GetBasePath','Rest', 'Wait', '$state',
        'ProcessErrors', 'Prompt', 'Find', '$location', '$filter',
        function(GetBasePath, Rest, Wait, $state, ProcessErrors, Prompt, Find,
            $location, $filter) {
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
                            if (new RegExp('/' + id + '$').test($location.$$url)) {
                                $location.url($location.url().replace(/[/][0-9]+$/, "")); // go to list view
                            }
                            else{
                                $state.go('.', null, {reload: true});
                            }
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
                    body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the schedule below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(schedule.name) + '</div>',
                    action: action,
                    actionText: 'DELETE',
                    backdrop: false
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
        }]);
