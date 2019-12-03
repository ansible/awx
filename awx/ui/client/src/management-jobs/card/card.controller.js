/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    [   'Wait',  'CreateDialog', 'GetBasePath' ,
        'Rest' ,
        'ProcessErrors', '$rootScope', '$state',
        '$scope', 'CreateSelect2', 'i18n', '$transitions',
        function( Wait, CreateDialog, GetBasePath,
            Rest, ProcessErrors,
            $rootScope, $state, $scope,
            CreateSelect2, i18n, $transitions) {

                var defaultUrl = GetBasePath('system_job_templates') + "?order_by=name";

                var getManagementJobs = function(){
                    Rest.setUrl(defaultUrl);
                    Rest.get()
                        .then(({data}) => {
                            $scope.mgmtCards = data.results;
                            Wait('stop');
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, null, {hdr: i18n._('Error!'),
                            msg: i18n.sprintf(i18n._('Call to %s failed. Return status: %d'), (defaultUrl === undefined) ? "undefined" : defaultUrl, status )});
                        });
                };
                getManagementJobs();

                // This handles the case where the user refreshes the management job notifications page.
                if($state.current.name === 'managementJobsList.notifications') {
                    $scope.activeCard = parseInt($state.params.management_id);
                    $scope.cardAction = "notifications";
                }

                $scope.goToNotifications = function(card){
                    $state.transitionTo('managementJobsList.notifications',{
                        card: card,
                        management_id: card.id
                    });
                };

                var launchManagementJob = function (defaultUrl){
                  var data = {};
                  Rest.setUrl(defaultUrl);
                  Rest.post(data)
                      .then(({data}) => {
                          Wait('stop');
                          $state.go('output', { id: data.system_job, type: 'system' }, { reload: true });
                      })
                      .catch(({data, status}) => {
                          let template_id = $scope.job_template_id;
                          template_id = (template_id === undefined) ? "undefined" : i18n.sprintf("%d", template_id);
                          ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                              msg: i18n.sprintf(i18n._('Failed updating job %s with variables. POST returned: %d'), template_id, status) });
                      });
                };

                $scope.submitJob = function (id, name) {
                    Wait('start');
                        defaultUrl = GetBasePath('system_job_templates')+id+'/launch/';
                        var noModalJobs = ['Cleanup Expired Sessions', 'Cleanup Expired OAuth 2 Tokens'];
                        if (noModalJobs.includes(name)) {
                            launchManagementJob(defaultUrl, name);
                        } else {
                            
                            CreateDialog({
                                id: 'prompt-for-days',
                                title: name,
                                scope: $scope,
                                width: 500,
                                height: 300,
                                minWidth: 200,
                                callback: 'PromptForDays',
                                resizable: false,
                                onOpen: function(){
                                    $scope.$watch('prompt_for_days_form.$invalid', function(invalid) {
                                        if (invalid === true) {
                                            $('#prompt-for-days-launch').prop("disabled", true);
                                        } else {
                                            $('#prompt-for-days-launch').prop("disabled", false);
                                        }
                                    });

                                    let fieldScope = $scope.$parent;
                                    fieldScope.days_to_keep = 30;
                                    $scope.prompt_for_days_form.$setPristine();
                                    $scope.prompt_for_days_form.$invalid = false;
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
                                        const extra_vars = {"days": $scope.days_to_keep },
                                        data = {};
                                        data.extra_vars = JSON.stringify(extra_vars);

                                        Rest.setUrl(defaultUrl);
                                        Rest.post(data)
                                            .then(({data}) => {
                                                Wait('stop');
                                                $("#prompt-for-days").dialog("close");
                                                // $("#configure-dialog").dialog('close');
                                                $state.go('output', { id: data.system_job, type: 'system' }, { reload: true });
                                            })
                                            .catch(({data, status}) => {
                                                let template_id = $scope.job_template_id;
                                                template_id = (template_id === undefined) ? "undefined" : i18n.sprintf("%d", template_id);
                                                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                                                    msg: i18n.sprintf(i18n._('Failed updating job %s with variables. POST returned: %d'), template_id, status) });
                                            });
                                    },
                                    "class": "btn btn-primary",
                                    "id": "prompt-for-days-launch"
                                }
                                ]
                            });
                        }

                        if ($scope.removePromptForDays) {
                            $scope.removePromptForDays();
                        }
                        $scope.removePromptForDays = $scope.$on('PromptForDays', function() {
                            // $('#configure-dialog').dialog('close');
                            $('#prompt-for-days').show();
                            $('#prompt-for-days').dialog('open');
                            Wait('stop');
                        });
                };

                $scope.configureSchedule = function(id) {
                    $state.transitionTo('managementJobsList.schedule', {
                        id: id
                    });
                };

                var cleanUpStateChangeListener = $transitions.onSuccess({}, function(trans) {
                     if(trans.to().name === "managementJobsList") {
                         // We are on the management job list view - nothing needs to be highlighted
                         delete $scope.activeCard;
                         delete $scope.cardAction;
                     }
                     else if(trans.to().name === "managementJobsList.notifications") {
                         // We are on the notifications view - update the active card and the action
                         $scope.activeCard = parseInt(trans.params('to').management_id);
                         $scope.cardAction = "notifications";
                     }
                });

                // Remove the listener when the scope is destroyed to avoid a memory leak
                $scope.$on('$destroy', function() {
                    cleanUpStateChangeListener();
                });
        }
    ];
