/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    [   'Wait',  'CreateDialog', 'GetBasePath' ,
        'Rest' ,
        'ProcessErrors', '$rootScope', '$state',
        '$scope', 'CreateSelect2', 'i18n',
        function( Wait, CreateDialog, GetBasePath,
            Rest, ProcessErrors,
            $rootScope, $state, $scope,
            CreateSelect2, i18n) {

                var defaultUrl = GetBasePath('system_job_templates') + "?order_by=name";

                var getManagementJobs = function(){
                    Rest.setUrl(defaultUrl);
                    Rest.get()
                        .success(function(data){
                            $scope.mgmtCards = data.results;
                            Wait('stop');
                        })
                        .error(function(data, status){
                            ProcessErrors($scope, data, status, null, {hdr: i18n._('Error!'),
                            msg: i18n.sprintf(i18n._('Call to %s failed. Return status: %d'), (defaultUrl === undefined) ? "undefined" : defaultUrl, status )});
                        });
                };
                getManagementJobs();
                var scope = $rootScope.$new();
                scope.cleanupJob = true;

                // This handles the case where the user refreshes the management job notifications page.
                if($state.current.name === 'managementJobsList.notifications') {
                    $scope.activeCard = parseInt($state.params.management_id);
                    $scope.cardAction = "notifications";
                }

                 // Cancel
                scope.cancelConfigure = function () {
                    try {
                        $('#configure-dialog').dialog('close');
                        $("#configure-save-button").remove();
                    }
                    catch(e) {
                        //ignore
                    }

                    Wait('stop');
                };

                $scope.submitCleanupJob = function(id, name){
                    defaultUrl = GetBasePath('system_job_templates')+id+'/launch/';
                    CreateDialog({
                        id: 'prompt-for-days-facts',
                        title: name,
                        scope: scope,
                        width: 500,
                        height: 470,
                        minWidth: 200,
                        callback: 'PromptForDaysFacts',
                        resizable: false,
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
                        buttons: [
                            {
                                "label": "Cancel",
                                "onClick": function() {
                                    $(this).dialog('close');
                                },
                                "class": "btn btn-default",
                                "id": "prompt-for-days-facts-cancel"
                            },
                            {
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
                                        .success(function(data) {
                                            Wait('stop');
                                            $("#prompt-for-days-facts").dialog("close");
                                            $("#configure-dialog").dialog('close');
                                            $state.go('managementJobStdout', {id: data.system_job}, {reload:true});
                                        })
                                        .error(function(data, status) {
                                            let template_id = scope.job_template_id;
                                            template_id = (template_id === undefined) ? "undefined" : i18n.sprintf("%d", template_id);
                                            ProcessErrors(scope, data, status, null, { hdr: i18n._('Error!'),
                                                msg: i18n.sprintf(i18n._('Failed updating job %s with variables. POST returned: %d'), template_id, status) });
                                        });
                                },
                                "class": "btn btn-primary",
                                "id": "prompt-for-days-facts-launch",
                            }
                            ]
                    });

                    if (scope.removePromptForDays) {
                        scope.removePromptForDays();
                    }
                    scope.removePromptForDays = scope.$on('PromptForDaysFacts', function() {
                        // $('#configure-dialog').dialog('close');
                        $('#prompt-for-days-facts').show();
                        $('#prompt-for-days-facts').dialog('open');
                        CreateSelect2({
                            element: '#keep_unit',
                            multiple: false
                        });
                        CreateSelect2({
                            element: '#granularity_keep_unit',
                            multiple: false
                        });
                        Wait('stop');
                    });
                };

                $scope.goToNotifications = function(card){
                    $state.transitionTo('managementJobsList.notifications',{
                        card: card,
                        management_id: card.id
                    });
                };

                $scope.submitJob = function (id, name) {
                    Wait('start');
                        defaultUrl = GetBasePath('system_job_templates')+id+'/launch/';
                        CreateDialog({
                            id: 'prompt-for-days'    ,
                            title: name,
                            scope: scope,
                            width: 500,
                            height: 300,
                            minWidth: 200,
                            callback: 'PromptForDays',
                            resizable: false,
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
                            buttons: [
                                {
                                    "label": "Cancel",
                                    "onClick": function() {
                                        $(this).dialog('close');

                                    },
                                    "class": "btn btn-default",
                                    "id": "prompt-for-days-cancel"
                                },
                            {
                                "label": "Launch",
                                "onClick": function() {
                                    var extra_vars = {"days": scope.days_to_keep },
                                    data = {};
                                    data.extra_vars = JSON.stringify(extra_vars);

                                    Rest.setUrl(defaultUrl);
                                    Rest.post(data)
                                        .success(function(data) {
                                            Wait('stop');
                                            $("#prompt-for-days").dialog("close");
                                            // $("#configure-dialog").dialog('close');
                                            $state.go('managementJobStdout', {id: data.system_job}, {reload:true});
                                        })
                                        .error(function(data, status) {
                                            let template_id = scope.job_template_id;
                                            template_id = (template_id === undefined) ? "undefined" : i18n.sprintf("%d", template_id);
                                            ProcessErrors(scope, data, status, null, { hdr: i18n._('Error!'),
                                                msg: i18n.sprintf(i18n._('Failed updating job %s with variables. POST returned: %d'), template_id, status) });
                                        });
                                },
                                "class": "btn btn-primary",
                                "id": "prompt-for-days-launch"
                            }
                            ]
                        });

                        if (scope.removePromptForDays) {
                            scope.removePromptForDays();
                        }
                        scope.removePromptForDays = scope.$on('PromptForDays', function() {
                            // $('#configure-dialog').dialog('close');
                            $('#prompt-for-days').show();
                            $('#prompt-for-days').dialog('open');
                            Wait('stop');
                        });
                };

                $scope.chooseRunJob = function(id, name) {
                    if(this.card.job_type === "cleanup_facts") {
                        // Run only for 'Cleanup Fact Details'
                        $scope.submitCleanupJob(id, name);
                    } else {
                        $scope.submitJob(id, name);
                    }
                };

                $scope.configureSchedule = function(id) {
                    $state.transitionTo('managementJobsList.schedule', {
                        id: id
                    });
                };

                var cleanUpStateChangeListener = $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
                     if(toState.name === "managementJobsList") {
                         // We are on the management job list view - nothing needs to be highlighted
                         delete $scope.activeCard;
                         delete $scope.cardAction;
                     }
                     else if(toState.name === "managementJobsList.notifications") {
                         // We are on the notifications view - update the active card and the action
                         $scope.activeCard = parseInt(toParams.management_id);
                         $scope.cardAction = "notifications";
                     }
                });

                // Remove the listener when the scope is destroyed to avoid a memory leak
                $scope.$on('$destroy', function() {
                    cleanUpStateChangeListener();
                });
        }
    ];
