/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import listGenerator from 'tower/shared/list-generator/main';

export default
    [   'Wait', '$location' , '$compile',  'CreateDialog', 'generateList',
        'GetBasePath' , 'SearchInit' , 'PaginateInit',
        'SchedulesList',
        'Rest' , 'ProcessErrors', 'managementJobsListObject', '$rootScope',
        '$state',
        function( Wait, $location, $compile, CreateDialog, GenerateList,
            GetBasePath, SearchInit, PaginateInit,
            SchedulesList,
            Rest, ProcessErrors, managementJobsListObject, $rootScope,
            $state) {

                var scope = $rootScope.$new(),
                    parent_scope = scope,
                    defaultUrl = GetBasePath('system_job_templates'),
                    list = managementJobsListObject,
                    view = GenerateList;

                scope.cleanupJob = true;

                view.inject( list, {
                    mode: 'edit',
                    scope: scope,
                    showSearch: true
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
                            scope.$watch('prompt_for_days_facts_form.$invalid', function(invalid) {
                                if (invalid === true) {
                                    $('#prompt-for-days-facts-launch').prop("disabled", true);
                                } else {
                                    $('#prompt-for-days-facts-launch').prop("disabled", false);
                                }
                            });

                            var fieldScope = scope.$parent;

                            // set these form elements up on the scope where the form
                            // is the parent of the current scope
                            fieldScope.keep_unit_choices = [{
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
                            fieldScope.granularity_keep_unit_choices =  [{
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
                            scope.prompt_for_days_facts_form.$setPristine();
                            scope.prompt_for_days_facts_form.$invalid = false;
                            fieldScope.keep_unit =  fieldScope.keep_unit_choices[0];
                            fieldScope.granularity_keep_unit = fieldScope.granularity_keep_unit_choices[1];
                            fieldScope.keep_amount = 30;
                            fieldScope.granularity_keep_amount = 1;
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
                                scope.$watch('prompt_for_days_form.$invalid', function(invalid) {
                                    if (invalid === true) {
                                        $('#prompt-for-days-launch').prop("disabled", true);
                                    } else {
                                        $('#prompt-for-days-launch').prop("disabled", false);
                                    }
                                });

                                var fieldScope = scope.$parent;
                                fieldScope.days_to_keep = 30;
                                scope.prompt_for_days_form.$setPristine();
                                scope.prompt_for_days_form.$invalid = false;
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
                                            // $("#configure-tower-dialog").dialog('close');
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

                scope.configureSchedule = function() {
                    $state.transitionTo('managementJobsSchedule', {
                        management_job: this.configure_job,
                        management_job_id: this.configure_job.id
                    });
                };

                parent_scope.refreshJobs = function(){
                    scope.search(SchedulesList.iterator);
                };
        }
    ];
