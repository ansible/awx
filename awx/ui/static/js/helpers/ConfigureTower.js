/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
    /**
 * @ngdoc function
 * @name helpers.function:Schedules
 * @description
 *  Schedules Helper
 *
 *  Display the scheduler widget in a dialog
 *
 */

'use strict';

angular.module('ConfigureTowerHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'ModalDialog',
    'GeneratorHelpers'])

    .factory('ConfigureTower', ['Wait', 'CreateDialog', 'ConfigureTowerJobsList', 'GenerateList', 'GetBasePath' , 'SearchInit' , 'PaginateInit', 'PlaybookRun', 'LoadSchedulesScope',
        'SchedulesList', 'SchedulesControllerInit' , 'ConfigureTowerSchedule', 'Rest' , 'ProcessErrors',
        function(Wait, CreateDialog, ConfigureTowerJobsList, GenerateList, GetBasePath, SearchInit, PaginateInit, PlaybookRun, LoadSchedulesScope,
            SchedulesList, SchedulesControllerInit, ConfigureTowerSchedule, Rest, ProcessErrors) {
        return function(params) {
            // Set modal dimensions based on viewport width

            var scope = params.scope.$new(),
                callback = 'OpenConfig',
                defaultUrl = GetBasePath('system_job_templates'),
                list = ConfigureTowerJobsList,
                view = GenerateList,
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
                // parent_scope: parent_scope,
                // list: list
            });


            CreateDialog({
                id: 'configure-tower-dialog',
                title: 'Configure Tower',
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

            scope.submitJob = function (id) {
                Wait('start');
                scheduleUrl += id+'/launch/';
                CreateDialog({
                    id: 'prompt-for-days'    ,
                    title: "Cleanup Job",
                    scope: scope,
                    width: 500,
                    height: 300,
                    minWidth: 200,
                    callback: 'PromptForDays',
                    buttons: [{
                        "label": "Cancel",
                        "onClick": function() {
                            $(this).dialog('close');

                        },
                        "icon": "fa-times",
                        "class": "btn btn-default",
                        "id": "prompt-for-days-button"
                    },{
                        "label": "Launch",
                        "onClick": function() {
                            var extra_vars = {"days": $("#days_to_keep").val() },
                            data = {};
                            data.extra_vars = JSON.stringify(extra_vars);

                            Rest.setUrl(scheduleUrl);
                            Rest.post(data)
                                .success(function() {
                                    Wait('stop');
                                    $("#prompt-for-days").dialog("close");
                                    $("#configure-tower-dialog").dialog('close');
                                })
                                .error(function(data, status) {
                                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
                                });
                        },
                        "icon":  "fa-rocket",
                        "class": "btn btn-primary",
                        "id": "prompt-for-days-button"
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



            };

            scope.configureSchedule = function(id) {
                // scope.addSchedule();
                // schedule_scope.editSchedule = function(id) {
                //     GroupsScheduleEdit({ scope: schedule_scope, mode: 'edit', url: GetBasePath('schedules') + id + '/' });
                // };

                // schedule_scope.addSchedule = function() {
                //     GroupsScheduleEdit({ scope: schedule_scope, mode: 'add', url: url });
                // };
                Rest.setUrl(scheduleUrl+id+'/schedules/');
                Rest.get()
                    .success(function(data) {
                        if(data.count>0){
                            scope.days=data.results[0].extra_data.days;
                            ConfigureTowerSchedule({
                                scope: scope,
                                mode: 'edit',
                                url: scheduleUrl+id+'/schedules/',
                                // id: id
                            });
                        } else {
                            ConfigureTowerSchedule({
                                scope: scope,
                                mode: 'add',
                                url: scheduleUrl+id+'/schedules/'
                            });
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
                    });

            };

            // scope.deleteSystemSchedule = function(id){
            //     Rest.setUrl(scheduleUrl+id+'/schedules/');
            //     Rest.get()
            //         .success(function(data) {


            //         })
            //         .error(function(data, status) {
            //             ProcessErrors(scope, data, status, null, { hdr: 'Error!',
            //                 msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
            //         });





            //     Rest.setUrl(GetBasePath('schedules')+id+'/');
            //     Rest.destroy()
            //         .success(function() {
            //             Alert("successfully deleted");
            //         })
            //         .error(function(data, status) {
            //             ProcessErrors(scope, data, status, null, { hdr: 'Error!',
            //                 msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
            //         });
            // };

        };
    }])


.factory('ConfigureTowerSchedule', ['$compile','SchedulerInit', 'Rest', 'Wait', 'SetSchedulesInnerDialogSize', 'SchedulePost', 'ProcessErrors', 'GetBasePath', 'Empty',
function($compile, SchedulerInit, Rest, Wait, SetSchedulesInnerDialogSize, SchedulePost, ProcessErrors, GetBasePath, Empty) {
    return function(params) {
        var parent_scope = params.scope,
            mode = params.mode,  // 'add' or 'edit'
            url = params.url,
            scope = parent_scope.$new(),
            id = params.id || undefined,
            schedule = {},
            scheduler,
            target,
            showForm,
            list,
            detail,
            restoreList,
            container,
            elem;

// <div id='configure-tower-dialog' style="display:none">
//       <div id="configure-jobs-list"></div>
//       <div id="configure-schedule-form"></div>
//     </div>

        // Wait('start');
        // detail = $('#schedules-detail').hide();
        // list = $('#schedules-list');
        // target = $('#schedules-form');
        // container = $('#schedules-form-container');

        Wait('start');
        // $('#configure-jobs').hide();
        detail = $('#configure-schedules-detail').hide();
        list = $('#configure-schedules-list');
        target = $('#configure-schedules-form');
        container = $('#configure-schedules-form-container');
        $("#configure-jobs").show();
        $("#configure-schedules-form-container").hide();

        // Clean up any lingering stuff
        container.hide();
        target.empty();
        $('.tooltip').each(function () {
            $(this).remove();
        });
        $('.popover').each(function () {
            $(this).remove();
        });

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
                // $('#configure-save-button').prop('disabled', true);
                target.show();
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
            container.hide('slide', { direction: 'left' }, 500, restoreList);
            scope.$destroy();
        });

        scope.saveScheduleForm = function() {
            var extra_vars;
            if (scheduler.isValid()) {
                scope.schedulerIsValid = true;
                url = (mode==="edit") ? GetBasePath('schedules')+id+'/' : url;

                extra_vars = {
                    "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                };
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

        scope.cancelScheduleForm = function() {
            container.hide('slide', { direction: 'right' }, 500, restoreList);
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
