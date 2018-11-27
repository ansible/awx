/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Schedules
 * @description This controller's for schedules
 */


export default [
    '$filter', '$scope', '$location', '$stateParams', 'ScheduleList', 'Rest',
    'rbacUiControlService', 'JobTemplateModel', 'ToggleSchedule', 'DeleteSchedule',
    '$q', '$state', 'Dataset', 'ParentObject', 'UnifiedJobsOptions', 'i18n', 'SchedulerStrings',
    function($filter, $scope, $location, $stateParams, ScheduleList, Rest,
        rbacUiControlService, JobTemplate, ToggleSchedule, DeleteSchedule,
        $q, $state, Dataset, ParentObject, UnifiedJobsOptions, i18n, strings
    ) {

        var base, scheduleEndpoint,
            list = ScheduleList;

        init();

        function init() {
            if (ParentObject){
                $scope.parentObject = ParentObject;
                scheduleEndpoint = ParentObject.endpoint|| ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;
                $scope.canAdd = false;
                rbacUiControlService.canAdd(scheduleEndpoint)
                    .then(function(params) {
                        $scope.canAdd = params.canAdd;
                    });
                if (_.has(ParentObject, 'type') && ParentObject.type === 'job_template') {
                    const jobTemplate = new JobTemplate();
                    jobTemplate.getLaunch(ParentObject.id)
                        .then(({data}) => {
                            if (data.passwords_needed_to_start &&
                                data.passwords_needed_to_start.length > 0 &&
                                !ParentObject.ask_credential_on_launch
                            ) {
                                $scope.credentialRequiresPassword = true;
                                $scope.addTooltip = i18n._("Using a credential that requires a password on launch is prohibited when creating a Job Template schedule");
                            }
                        });
                }
            }

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            $scope.unified_job_options = UnifiedJobsOptions.actions.GET;

            // _.forEach($scope[list.name], buildTooltips);
        }

        $scope.isValid = (schedule) => {
            let type = schedule.summary_fields.unified_job_template.unified_job_type;
            switch(type){
                case 'job':
                    return _.every(['project', 'inventory'], _.partial(_.has, schedule.related));
                case 'project_update':
                    return _.has(schedule, 'related.project');
                case 'inventory_update':
                    return _.has(schedule, 'related.inventory');
                default:
                    return true;
            }
        };

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
            $scope[list.name].forEach(function(item, item_idx) {
                var itm = $scope[list.name][item_idx];

                // Set the item type label
                if (list.fields.type && $scope.unified_job_options &&
                    $scope.unified_job_options.hasOwnProperty('type')) {
                        $scope.unified_job_options.type.choices.every(function(choice) {
                            if (choice[0] === itm.summary_fields.unified_job_template.unified_job_type) {
                            itm.type_label = choice[1];
                            return false;
                        }
                        return true;
                    });
                }
                buildTooltips(itm);

                let stateParams = { schedule_id: item.id };
                let route = '';
                if (item.summary_fields.unified_job_template) {
                    if (item.summary_fields.unified_job_template.unified_job_type === 'job') {
                        route = 'templates.editJobTemplate.schedules.edit';
                        stateParams.job_template_id = item.summary_fields.unified_job_template.id;
                    } else if (item.summary_fields.unified_job_template.unified_job_type === 'project_update') {
                        route = 'projects.edit.schedules.edit';
                        stateParams.project_id = item.summary_fields.unified_job_template.id;
                    } else if (item.summary_fields.unified_job_template.unified_job_type === 'workflow_job') {
                        route = 'templates.editWorkflowJobTemplate.schedules.edit';
                        stateParams.workflow_job_template_id = item.summary_fields.unified_job_template.id;
                    } else if (item.summary_fields.unified_job_template.unified_job_type === 'inventory_update') {
                        route = 'inventories.edit.inventory_sources.edit.schedules.edit';
                        stateParams.inventory_id = item.summary_fields.inventory.id;
                        stateParams.inventory_source_id = item.summary_fields.unified_job_template.id;
                    } else if (item.summary_fields.unified_job_template.unified_job_type === 'system_job') {
                        route = 'managementJobsList.schedule.edit';
                        stateParams.id = item.summary_fields.unified_job_template.id;
                    }
                }
                itm.route = route;
                itm.stateParams = stateParams;
                itm.linkToDetails = `${route}(${JSON.stringify(stateParams)})`;
            });
        }

        function buildTooltips(schedule) {
            var job = schedule.summary_fields.unified_job_template;
            if (schedule.enabled) {
                const tip = (schedule.summary_fields.user_capabilities.edit || $scope.credentialRequiresPassword) ? strings.get('list.SCHEDULE_IS_ACTIVE') : strings.get('list.SCHEDULE_IS_ACTIVE_CLICK_TO_STOP');
                schedule.play_tip = tip;
                schedule.status = 'active';
                schedule.status_tip = tip;
            } else {
                const tip = (schedule.summary_fields.user_capabilities.edit || $scope.credentialRequiresPassword) ? strings.get('list.SCHEDULE_IS_STOPPED') : strings.get('list.SCHEDULE_IS_STOPPED_CLICK_TO_STOP');//i18n._('Schedule is stopped.') : i18n._('Schedule is stopped. Click to activate.');
                schedule.play_tip = tip;
                schedule.status = 'stopped';
                schedule.status_tip = tip;
            }

            schedule.nameTip = $filter('sanitize')(schedule.name);
            // include the word schedule if the schedule name does not include the word schedule
            if (schedule.name.indexOf("schedule") === -1 && schedule.name.indexOf("Schedule") === -1) {
                schedule.nameTip += " schedule";
            }
            schedule.nameTip += " for ";
            if (job.name.indexOf("job") === -1 && job.name.indexOf("Job") === -1) {
                schedule.nameTip += "job ";
            }
            schedule.nameTip += $filter('sanitize')(job.name);
            schedule.nameTip += `. ${strings.get('list.CLICK_TO_EDIT')}`;
        }

        $scope.refreshSchedules = function() {
            $state.go('.', null, { reload: true });
        };

        $scope.addSchedule = function() {
            if($state.current.name.endsWith('.edit')) {
                $state.go('^.add');
            }
            if(!$state.current.name.endsWith('.add')) {
                $state.go('.add');
            }
        };

        $scope.editSchedule = function(schedule) {
            $state.go(schedule.route, schedule.stateParams);
        };

        $scope.toggleSchedule = function(event, id) {
            try {
                $(event.target).tooltip('hide');
            } catch (e) {
                // ignore
            }
            ToggleSchedule({
                scope: $scope,
                id: id
            });
        };

        $scope.deleteSchedule = function(id) {
            DeleteSchedule({
                scope: $scope,
                id: id
            });
        };

        base = $location.path().replace(/^\//, '').split('/')[0];

        if (base === 'management_jobs') {
            $scope.base = base = 'system_job_templates';
        }
        if ($stateParams.job_type) {
            $scope.job_type = $stateParams.job_type;
        }

        $scope.refreshJobs = function() {
            $state.go('.', null, { reload: true });
        };

        $scope.formCancel = function() {
            $state.go('^', null, { reload: true });
        };
    }
];
