/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name helpers.function:ConfigureTower
 * @description
 *  Schedules Helper
 *
 *  Display the scheduler widget in a dialog
 *
 */

import listGenerator from 'tower/shared/list-generator/main';

export default
    angular.module('ConfigureTowerHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', 'SearchHelper', 'PaginationHelpers', listGenerator.name, 'ModalDialog',
        'GeneratorHelpers'])

        .factory('ConfigureTower', ['Wait', '$location' , '$compile',  'CreateDialog', 'ConfigureTowerJobsList', 'generateList', 'GetBasePath' , 'SearchInit' , 'PaginateInit', 'PlaybookRun', 'LoadSchedulesScope',
            'SchedulesList', 'SchedulesControllerInit' , 'ConfigureTowerSchedule', 'Rest' , 'ProcessErrors',
            function(Wait, $location, $compile, CreateDialog, ConfigureTowerJobsList, GenerateList, GetBasePath, SearchInit, PaginateInit, PlaybookRun, LoadSchedulesScope,
                SchedulesList, SchedulesControllerInit, ConfigureTowerSchedule, Rest, ProcessErrors) {
            return function(params) {
                // Set modal dimensions based on viewport width

                var scope = params.scope.$new(),
                    parent_scope = params.scope,
                    callback = 'OpenConfig',
                    defaultUrl = GetBasePath('system_job_templates'),
                    list = ConfigureTowerJobsList,
                    view = GenerateList, e,
                    scheduleUrl = GetBasePath('system_job_templates'),
                    buttons = [
                    {
                        "label": "Close",
                        "onClick": function() {
                            // $(this).dialog('close');
                            scope.cancelConfigure();
                        },
                        "icon": "fa-times",
                        "class": "btn btn-default",
                        "id": "configure-close-button"
                    }
                ];

                scope.cleanupJob = true;

                if(scope.removeOpenConfig) {
                    scope.removeOpenConfig();
                }
                scope.removeOpenConfig = scope.$on('OpenConfig', function() {
                    $('#configure-tower-dialog').dialog('open');
                    $('#configure-close-button').focus();
                    $('#configure-close-button').blur();
                });

                view.inject( list, {
                    id : 'configure-jobs',
                    mode: 'edit',
                    scope: scope,
                    breadCrumbs: false,
                    showSearch: false
                });

                SearchInit({
                    scope: scope,
                    set: 'configure_jobs',
                    list: list,
                    url: defaultUrl
                });
                PaginateInit({
                    scope: scope,
                    list: list,
                    url: defaultUrl
                });

                scope.search(list.iterator);

                SchedulesControllerInit({
                    scope: scope,
                    parent_scope: parent_scope,
                    // list: list
                });


                CreateDialog({
                    id: 'configure-tower-dialog',
                    title: 'Management Jobs',
                    target: 'configure-tower-dialog',
                    scope: scope,
                    buttons: buttons,
                    width: 670,
                    height: 800,
                    minWidth: 400,
                    callback: callback,
                    onClose: function () {
                        // Destroy on close
                        $('.tooltip').each(function () {
                            // Remove any lingering tooltip <div> elements
                            $(this).remove();
                        });
                        $('.popover').each(function () {
                            // remove lingering popover <div> elements
                            $(this).remove();
                        });
                        $("#configure-jobs").show();
                        $("#configure-schedules-form-container").hide();
                        $('#configure-schedules-list').empty();
                        $('#configure-schedules-form').empty();
                        $('#configure-schedules-detail').empty();
                        $('#configure-tower-dialog').hide();
                        $(this).dialog('destroy');
                        scope.cancelConfigure();
                    },
                });



                 // Cancel
                scope.cancelConfigure = function () {
                    try {
                        $('#configure-tower-dialog').dialog('close');
                        $("#configure-save-button").remove();
                    }
                    catch(e) {
                        //ignore
                    }
                    if (scope.searchCleanup) {
                        scope.searchCleanup();
                    }
                    // if (!Empty(parent_scope) && parent_scope.restoreSearch) {
                    //     parent_scope.restoreSearch();
                    // }
                    else {
                        Wait('stop');
                    }
                };

                scope.submitCleanupJob = function(id, name){
                    defaultUrl = GetBasePath('system_job_templates')+id+'/launch/';
                    CreateDialog({
                        id: 'prompt-for-days-facts',
                        title: name,
                        scope: scope,
                        width: 500,
                        height: 470,
                        minWidth: 200,
                        callback: 'PromptForDaysFacts',
                        onOpen: function(){
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
                            e = angular.element(document.getElementById('prompt_for_days_facts_form'));
                            scope.prompt_for_days_facts_form.keep_amount.$setViewValue(30);
                            scope.prompt_for_days_facts_form.granularity_keep_amount.$setViewValue(1);
                            $compile(e)(scope);
                            scope.keep_unit = scope.keep_unit_choices[0];
                            scope.granularity_keep_unit = scope.granularity_keep_unit_choices[1];

                            // this is a work-around for getting awMax to work (without
                            // clearing out the form)
                            scope.$watch('keep_amount', function(newVal) {
                                if (!newVal && newVal !== 0) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (isNaN(newVal)) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (newVal < 0) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (newVal > 9999) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else {
                                    $('#prompt-for-days-facts-launch').prop("disabled", false);
                                }
                            });
                            scope.$watch('granularity_keep_amount', function(newVal2) {
                                if (!newVal2 && newVal2 !== 0) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (isNaN(newVal2)) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (newVal2 < 0) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else if (newVal2 > 9999) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else {
                                    $('#prompt-for-days-facts-launch').prop("disabled", false);
                                }
                            });
                        },
                        buttons: [{
                            "label": "Cancel",
                            "onClick": function() {
                                $(this).dialog('close');

                            },
                            "icon": "fa-times",
                            "class": "btn btn-default",
                            "id": "prompt-for-days-facts-cancel"
                        },{
                            "label": "Launch",
                            "onClick": function() {
                                var extra_vars = {
                                    "older_than": scope.keep_amount+scope.keep_unit.value,
                                    "granularity": scope.granularity_keep_amount+scope.granularity_keep_unit.value
                                },
                                data = {};
                                data.extra_vars = JSON.stringify(extra_vars);

                                Rest.setUrl(defaultUrl);
                                Rest.post(data)
                                    .success(function() {
                                        Wait('stop');
                                        $("#prompt-for-days-facts").dialog("close");
                                        $("#configure-tower-dialog").dialog('close');
                                        $location.path('/jobs/');
                                    })
                                    .error(function(data, status) {
                                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Failed updating job ' + scope.job_template_id + ' with variables. POST returned: ' + status });
                                    });
                            },
                            "icon":  "fa-rocket",
                            "class": "btn btn-primary",
                            "id": "prompt-for-days-facts-launch"
                        }]
                    });

                    if (scope.removePromptForDays) {
                        scope.removePromptForDays();
                    }
                    scope.removePromptForDays = scope.$on('PromptForDaysFacts', function() {
                        // $('#configure-tower-dialog').dialog('close');
                        $('#prompt-for-days-facts').show();
                        $('#prompt-for-days-facts').dialog('open');
                        Wait('stop');
                    });
                };

                scope.submitJob = function (id, name) {
                    Wait('start');
                    if(this.configure_job.job_type === "cleanup_facts"){
                        scope.submitCleanupJob(id, name);
                    }
                    else {
                        defaultUrl = GetBasePath('system_job_templates')+id+'/launch/';
                        CreateDialog({
                            id: 'prompt-for-days'    ,
                            title: name,
                            scope: scope,
                            width: 500,
                            height: 300,
                            minWidth: 200,
                            callback: 'PromptForDays',
                            onOpen: function(){
                                e = angular.element(document.getElementById('prompt_for_days_form'));
                                scope.prompt_for_days_form.days_to_keep.$setViewValue(30);
                                $compile(e)(scope);

                                // this is a work-around for getting awMax to work (without
                                // clearing out the form)
                                scope.$watch('days_to_keep', function(newVal) {   // oldVal, scope) { // unused params get caught by jshint
                                    if (!newVal && newVal !== 0) {
                                        $('#prompt-for-days-launch').prop("disabled", true);
                                    } else if (isNaN(newVal)) {
                                        $('#prompt-for-days-launch').prop("disabled", true);
                                    } else if (newVal < 0) {
                                        $('#prompt-for-days-launch').prop("disabled", true);
                                    } else if (newVal > 9999) {
                                        $('#prompt-for-days-launch').prop("disabled", true);
                                    } else {
                                        $('#prompt-for-days-launch').prop("disabled", false);
                                    }
                                });
                            },
                            buttons: [{
                                "label": "Cancel",
                                "onClick": function() {
                                    $(this).dialog('close');

                                },
                                "icon": "fa-times",
                                "class": "btn btn-default",
                                "id": "prompt-for-days-cancel"
                            },{
                                "label": "Launch",
                                "onClick": function() {
                                    var extra_vars = {"days": scope.days_to_keep },
                                    data = {};
                                    data.extra_vars = JSON.stringify(extra_vars);

                                    Rest.setUrl(defaultUrl);
                                    Rest.post(data)
                                        .success(function() {
                                            Wait('stop');
                                            $("#prompt-for-days").dialog("close");
                                            $("#configure-tower-dialog").dialog('close');
                                            $location.path('/jobs/');
                                        })
                                        .error(function(data, status) {
                                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                                msg: 'Failed updating job ' + scope.job_template_id + ' with variables. POST returned: ' + status });
                                        });
                                },
                                "icon":  "fa-rocket",
                                "class": "btn btn-primary",
                                "id": "prompt-for-days-launch"
                            }]
                        });

                        if (scope.removePromptForDays) {
                            scope.removePromptForDays();
                        }
                        scope.removePromptForDays = scope.$on('PromptForDays', function() {
                            // $('#configure-tower-dialog').dialog('close');
                            $('#prompt-for-days').show();
                            $('#prompt-for-days').dialog('open');
                            Wait('stop');
                        });
                    }
                };

                scope.configureSchedule = function(id, name) {
                    if (id === 4) {
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
                    } else {
                        scope.isFactCleanup = false;
                    }

                    Rest.setUrl(scheduleUrl+id+'/schedules/');
                    Rest.get()
                        .success(function(data) {
                            if(data.count>0){
                                scope.days=data.results[0].extra_data.days;
                                ConfigureTowerSchedule({
                                    scope: scope,
                                    mode: 'edit',
                                    url: scheduleUrl+id+'/schedules/'
                                });
                            } else {
                                ConfigureTowerSchedule({
                                    scope: scope,
                                    mode: 'add',
                                    url: scheduleUrl+id+'/schedules/',
                                    name: name
                                });
                            }
                        })
                        .error(function(data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed getting schedule information' });
                        });

                };

                parent_scope.refreshJobs = function(){
                    scope.search(SchedulesList.iterator);
                };

            };
        }])


    .factory('ConfigureTowerSchedule', ['$compile','SchedulerInit', 'Rest', 'Wait', 'SetSchedulesInnerDialogSize', 'SchedulePost', 'ProcessErrors', 'GetBasePath', 'Empty', 'Prompt',
    function($compile, SchedulerInit, Rest, Wait, SetSchedulesInnerDialogSize, SchedulePost, ProcessErrors, GetBasePath, Empty, Prompt) {
        return function(params) {
            var parent_scope = params.scope,
                mode = params.mode,  // 'add' or 'edit'
                url = params.url,
                scope = parent_scope.$new(),
                id = params.id || undefined,
                name = params.name || undefined,
                schedule = {},
                scheduler,
                target,
                showForm,
                list,
                detail,
                restoreList,
                container,
                elem;

            Wait('start');
            // $('#configure-jobs').hide();
            detail = $('#configure-schedules-detail').hide();
            list = $('#configure-schedules-list');
            target = $('#configure-schedules-form');
            container = $('#configure-schedules-form-container');
            $("#configure-jobs").show();
            $("#configure-schedules-form-container").hide();
            scope.mode = mode;
            // Clean up any lingering stuff
            container.hide();
            target.empty();
            $('.tooltip').each(function () {
                $(this).remove();
            });
            $('.popover').each(function () {
                $(this).remove();
            });

            $("#configure-cancel-button").after('<button type="button" class="btn btn-primary btn-sm" id="configure-save-button" ng-click="saveScheduleForm()" style="margin-left:5px"><i class="fa fa-check"></i> Save</button>');
            elem = angular.element(document.getElementById('configure-schedules-form-container'));
            $compile(elem)(scope);

            if (scope.removeScheduleReady) {
                scope.removeScheduleReady();
            }
            scope.removeScheduleReady = scope.$on('ScheduleReady', function() {
                // Insert the scheduler widget into the hidden div
                scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
                scheduler.inject('configure-schedules-form', false);
                scheduler.injectDetail('configure-schedules-detail', false);
                scheduler.clear();
                scope.formShowing = true;
                scope.showRRuleDetail = false;
                scope.schedulesTitle = (mode === 'edit') ? 'Edit Schedule' : 'Create Schedule';


                // display the scheduler widget
                showForm = function() {
                    $('#configure-jobs').show('slide', { direction: 'left' }, 500);
                    $('#configure-jobs').hide();
                    Wait('stop');
                    $('#configure-schedules-overlay').width($('#configure-schedules-tab')
                        .width()).height($('#configure-schedules-tab').height()).show();
                    container.width($('#configure-schedules-tab').width() - 18);
                    SetSchedulesInnerDialogSize();
                    container.show('slide', { direction: 'right' }, 300);
                    // scope.schedulerPurgeDays = (!Empty(scope.days)) ? Number(scope.days) : 30;
                    target.show();
                    if (scope.isFactCleanup) {
                        scope.$watch('scheduler_form.keep_amount.$modelValue', function(newVal) {
                            if (!newVal && newVal !== 0) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (isNaN(newVal)) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (newVal < 0) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (newVal > 9999) {
                                $('#configure-save-button').prop("disabled", true);
                            } else {
                                $('#configure-save-button').prop("disabled", false);
                            }
                        });
                        scope.$watch('scheduler_form.granularity_keep_amount.$modelValue', function(newVal2) {
                            if (!newVal2 && newVal2 !== 0) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (isNaN(newVal2)) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (newVal2 < 0) {
                                $('#configure-save-button').prop("disabled", true);
                            } else if (newVal2 > 9999) {
                                $('#configure-save-button').prop("disabled", true);
                            } else {
                                $('#configure-save-button').prop("disabled", false);
                            }
                        });
                    }
                    if(mode==="add"){
                        scope.$apply(function(){
                            scope.schedulerPurgeDays = 30;
                            scope.schedulerName = name+' Schedule';
                        });
                    }
                    if (mode === 'edit') {
                        scope.$apply(function() {
                            scheduler.setRRule(schedule.rrule);
                            scheduler.setName(schedule.name);
                            scope.schedulerPurgeDays = (!Empty(scope.days)) ? Number(scope.days) : 30;
                        });
                    }
                };
                setTimeout(function() { showForm(); }, 1000);
            });

            restoreList = function() {
                // $('#group-save-button').prop('disabled', false);
                $('#configure-jobs').show('slide', { direction: 'right' }, 500);
                // $('#configure-jobs').width($('#configure-jobs').width()).height($('#configure-jobs').height()).hide();
                // parent_scope.refreshSchedules();
                list.show('slide', { direction: 'right' }, 500);
                $('#configure-schedules-overlay').width($('#configure-schedules-tab').width()).height($('#configure-schedules-tab').height()).hide();
                parent_scope.refreshSchedules();

            };

            scope.showScheduleDetail = function() {
                if (scope.formShowing) {
                    if (scheduler.isValid()) {
                        detail.width($('#configure-schedules-form').width()).height($('#configure-schedules-form').height());
                        target.hide();
                        detail.show();
                        scope.formShowing = false;
                    }
                }
                else {
                    detail.hide();
                    target.show();
                    scope.formShowing = true;
                }
            };

            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
                Wait('stop');
                $("#configure-save-button").remove();
                container.hide('slide', { direction: 'left' }, 500, restoreList);
                scope.$destroy();
            });

            scope.saveScheduleForm = function() {
                var extra_vars;
                if (scheduler.isValid()) {
                    scope.schedulerIsValid = true;
                    url = (mode==="edit") ? GetBasePath('schedules')+id+'/' : url;
                    if (scope.isFactCleanup) {
                        extra_vars = {
                            "older_than": scope.keep_amount+scope.keep_unit.value,
                            "granularity": scope.granularity_keep_amount+scope.granularity_keep_unit.value
                        };
                    } else {
                        extra_vars = {
                            "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                        };
                    }
                    schedule.extra_data = JSON.stringify(extra_vars);

                    SchedulePost({
                        scope: scope,
                        url: url,
                        scheduler: scheduler,
                        callback: 'ScheduleSaved',
                        mode: mode,
                        schedule: schedule
                    });
                }
                else {
                    scope.schedulerIsValid = false;
                }
            };

            scope.deleteSystemSchedule = function(){
                var hdr = 'Delete Schedule',
                action = function () {
                    Wait('start');
                    Rest.setUrl(schedule.url);
                    Rest.destroy()
                        .success(function () {
                            $('#prompt-modal').modal('hide');
                            Wait('stop');
                            // scope.$emit(callback, id);
                            scope.cancelScheduleForm();
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
                    body: "<div class=\"alert alert-info\">Are you sure you want to delete the <em>" + scope.schedulerName  + "</em> schedule?</div>",
                    action: action,
                    backdrop: false
                });
            };

            scope.cancelScheduleForm = function() {
                container.hide('slide', { direction: 'right' }, 500, restoreList);
                $("#configure-save-button").remove();
                scope.$destroy();
            };

            if (mode === 'edit') {
                // Get the existing record
                Rest.setUrl(url); //GetBasePath('schedules')+id+'/');
                Rest.get()
                    .success(function(data) {
                        schedule = data.results[0];
                        id = schedule.id;
                        if (!/DTSTART/.test(schedule.rrule)) {
                            schedule.rrule += ";DTSTART=" + schedule.dtstart.replace(/\.\d+Z$/,'Z');
                        }
                        schedule.rrule = schedule.rrule.replace(/ RRULE:/,';');
                        schedule.rrule = schedule.rrule.replace(/DTSTART:/,'DTSTART=');
                        scope.$emit('ScheduleReady');
                    })
                    .error(function(data,status){
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                    });
            }
            else {
                scope.$emit('ScheduleReady');
            }
        };
    }]);
