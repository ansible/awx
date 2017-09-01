/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$log', 'Rest', 'Alert',
    'ProjectList', 'Prompt', 'ProcessErrors', 'GetBasePath', 'ProjectUpdate',
    'Wait', 'Empty', 'Find', 'GetProjectIcon', 'GetProjectToolTip', '$filter',
    '$state', 'rbacUiControlService', 'Dataset', 'i18n', 'QuerySet',
    function($scope, $rootScope, $log, Rest, Alert, ProjectList,
    Prompt, ProcessErrors, GetBasePath, ProjectUpdate, Wait, Empty, Find,
    GetProjectIcon, GetProjectToolTip, $filter, $state, rbacUiControlService,
    Dataset, i18n, qs) {

        var list = ProjectList,
            defaultUrl = GetBasePath('projects');

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd('projects')
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                });

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            _.forEach($scope[list.name], buildTooltips);
            $rootScope.flashMessage = null;
        }

        $scope.$on(`${list.iterator}_options`, function(event, data){
            $scope.options = data.data.actions.GET;
            optionsRequestDataProcessing();
        });

        $scope.$watchCollection(`${$scope.list.name}`, function() {
                optionsRequestDataProcessing();
            }
        );

        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            if ($scope[list.name] !== undefined) {
                $scope[list.name].forEach(function(item, item_idx) {
                    var itm = $scope[list.name][item_idx];

                    // Set the item type label
                    if (list.fields.scm_type && $scope.options &&
                            $scope.options.hasOwnProperty('scm_type')) {
                                $scope.options.scm_type.choices.forEach(function(choice) {
                                    if (choice[0] === item.scm_type) {
                                    itm.type_label = choice[1];
                                }
                            });
                        }

                        buildTooltips(itm);

                });
            }
        }

        function buildTooltips(project) {
            project.statusIcon = GetProjectIcon(project.status);
            project.statusTip = GetProjectToolTip(project.status);
            project.scm_update_tooltip = i18n._("Start an SCM update");
            project.scm_schedule_tooltip = i18n._("Schedule future SCM updates");
            project.scm_type_class = "";

            if (project.status === 'failed' && project.summary_fields.last_update && project.summary_fields.last_update.status === 'canceled') {
                project.statusTip = i18n._('Canceled. Click for details');
                project.scm_type_class = "btn-disabled";
            }

            if (project.status === 'running' || project.status === 'updating') {
                project.scm_update_tooltip = i18n._("SCM update currently running");
                project.scm_type_class = "btn-disabled";
            }
            if (project.scm_type === 'manual') {
                project.scm_update_tooltip = i18n._('Manual projects do not require an SCM update');
                project.scm_schedule_tooltip = i18n._('Manual projects do not require a schedule');
                project.scm_type_class = 'btn-disabled';
                project.statusTip = i18n._('Not configured for SCM');
                project.statusIcon = 'none';
            }
        }

        $scope.reloadList = function(){
            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            qs.search(path, $state.params[`${list.iterator}_search`])
            .then(function(searchResponse) {
                $scope[`${list.iterator}_dataset`] = searchResponse.data;
                $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            });
        };

        $scope.$on(`ws-jobs`, function(e, data) {
            var project;
            $log.debug(data);
            if ($scope.projects) {
                // Assuming we have a list of projects available
                project = Find({ list: $scope.projects, key: 'id', val: data.project_id });
                if (project) {
                    // And we found the affected project
                    $log.debug('Received event for project: ' + project.name);
                    $log.debug('Status changed to: ' + data.status);
                    if (data.status === 'successful' || data.status === 'failed' || data.status === 'canceled') {
                        $scope.reloadList();
                    } else {
                        project.scm_update_tooltip = "SCM update currently running";
                        project.scm_type_class = "btn-disabled";
                    }
                    project.status = data.status;
                    project.statusIcon = GetProjectIcon(data.status);
                    project.statusTip = GetProjectToolTip(data.status);
                }
            }
        });

        $scope.addProject = function() {
            $state.go('projects.add');
        };

        $scope.editProject = function(id) {
            $state.go('projects.edit', { project_id: id });
        };

        if ($scope.removeGoTojobResults) {
            $scope.removeGoTojobResults();
        }
        $scope.removeGoTojobResults = $scope.$on('GoTojobResults', function(e, data) {
            if (data.summary_fields.current_update || data.summary_fields.last_update) {

                Wait('start');

                // Grab the id from summary_fields
                var id = (data.summary_fields.current_update) ? data.summary_fields.current_update.id : data.summary_fields.last_update.id;

                $state.go('scmUpdateStdout', { id: id });

            } else {
                Alert(i18n._('No Updates Available'), i18n._('There is no SCM update information available for this project. An update has not yet been ' +
                    ' completed.  If you have not already done so, start an update for this project.'), 'alert-info');
            }
        });

        $scope.showSCMStatus = function(id) {
            // Refresh the project list
            var project = Find({ list: $scope.projects, key: 'id', val: id });
            if (Empty(project.scm_type) || project.scm_type === 'Manual') {
                Alert(i18n._('No SCM Configuration'), i18n._('The selected project is not configured for SCM. To configure for SCM, edit the project and provide SCM settings, ' +
                    'and then run an update.'), 'alert-info');
            } else {
                // Refresh what we have in memory to insure we're accessing the most recent status record
                Rest.setUrl(project.url);
                Rest.get()
                    .success(function(data) {
                        $scope.$emit('GoTojobResults', data);
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                            msg: i18n._('Project lookup failed. GET returned: ') + status });
                    });
            }
        };

        $scope.deleteProject = function(id, name) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function() {

                        let reloadListStateParams = null;

                        if($scope.projects.length === 1 && $state.params.project_search && !_.isEmpty($state.params.project_search.page) && $state.params.project_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.project_search.page = (parseInt(reloadListStateParams.project_search.page)-1).toString();
                        }

                        if (parseInt($state.params.project_id) === id) {
                            $state.go("^", reloadListStateParams, { reload: true });
                        } else {
                            $state.go('.', reloadListStateParams, {reload: true});
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                            msg: i18n.sprintf(i18n._('Call to %s failed. DELETE returned status: '), url) + status });
                    })
                    .finally(function() {
                        Wait('stop');
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete the project below?') + '</div>' + '<div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: 'DELETE'
            });
        };

        if ($scope.removeCancelUpdate) {
            $scope.removeCancelUpdate();
        }
        $scope.removeCancelUpdate = $scope.$on('Cancel_Update', function(e, url) {
            // Cancel the project update process
            Rest.setUrl(url);
            Rest.post()
                .success(function () {
                    Alert(i18n._('SCM Update Cancel'), i18n._('Your request to cancel the update was submitted to the task manager.'), 'alert-info');
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n.sprintf(i18n._('Call to %s failed. POST status: '), url) + status });
                });
        });

        if ($scope.removeCheckCancel) {
            $scope.removeCheckCancel();
        }
        $scope.removeCheckCancel = $scope.$on('Check_Cancel', function(e, data) {
            // Check that we 'can' cancel the update
            var url = data.related.cancel;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    if (data.can_cancel) {
                        $scope.$emit('Cancel_Update', url);
                    } else {
                        Alert(i18n._('Cancel Not Allowed'), '<div>' + i18n.sprintf(i18n._('Either you do not have access or the SCM update process completed. ' +
                            'Click the %sRefresh%s button to view the latest status.'), '<em>', '</em>') + '</div>', 'alert-info', null, null, null, null, true);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n.sprintf(i18n._('Call to %s failed. GET status: '), url) + status });
                });
        });

        $scope.cancelUpdate = function(project) {
            project.pending_cancellation = true;
            Rest.setUrl(GetBasePath("projects") + project.id);
            Rest.get()
                .success(function(data) {
                    if (data.related.current_update) {
                        Rest.setUrl(data.related.current_update);
                        Rest.get()
                            .success(function(data) {
                                $scope.$emit('Check_Cancel', data);
                            })
                            .error(function (data, status) {
                                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                                    msg: i18n.sprintf(i18n._('Call to %s failed. GET status: '), data.related.current_update) + status });
                            });
                    } else {
                        Alert(i18n._('Update Not Found'), '<div>' + i18n.sprintf(i18n._('An SCM update does not appear to be running for project: %s. Click the %sRefresh%s ' +
                            'button to view the latest status.'), $filter('sanitize')(name), '<em>', '</em>') + '</div>', 'alert-info',undefined,undefined,undefined,undefined,true);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                        msg: i18n._('Call to get project failed. GET status: ') + status });
                });
        };

        $scope.SCMUpdate = function(project_id, event) {
            try {
                $(event.target).tooltip('hide');
            } catch (e) {
                // ignore
            }
            $scope.projects.forEach(function(project) {
                if (project.id === project_id) {
                    if (project.scm_type === "Manual" || Empty(project.scm_type)) {
                        // Do not respond. Button appears greyed out as if it is disabled. Not disabled though, because we need mouse over event
                        // to work. So user can click, but we just won't do anything.
                        //Alert('Missing SCM Setup', 'Before running an SCM update, edit the project and provide the SCM access information.', 'alert-info');
                    } else if (project.status === 'updating' || project.status === 'running' || project.status === 'pending') {
                        // Alert('Update in Progress', 'The SCM update process is running. Use the Refresh button to monitor the status.', 'alert-info');
                    } else {
                        ProjectUpdate({ scope: $scope, project_id: project.id });
                    }
                }
            });
        };

        $scope.editSchedules = function(id) {
            var project = Find({ list: $scope.projects, key: 'id', val: id });
            if (!(project.scm_type === "Manual" || Empty(project.scm_type)) && !(project.status === 'updating' || project.status === 'running' || project.status === 'pending')) {
                $state.go('projectSchedules', { id: id });
            }
        };
    }
];
