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
    '$scope', '$compile', '$location', '$stateParams', 'SchedulesList', 'Rest',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'GetBasePath', 'Wait', 'rbacUiControlService',
    'Find', 'ToggleSchedule', 'DeleteSchedule', 'GetChoices', '$q', '$state', 'Dataset', 'ParentObject', 'UnifiedJobsOptions',
    function($scope, $compile, $location, $stateParams,
        SchedulesList, Rest, ProcessErrors, ReturnToCaller, ClearScope,
        GetBasePath, Wait, rbacUiControlService, Find,
        ToggleSchedule, DeleteSchedule, GetChoices,
        $q, $state, Dataset, ParentObject, UnifiedJobsOptions) {

        ClearScope();

        var base, scheduleEndpoint,
            list = SchedulesList;

        init();

        function init() {
            if (ParentObject){
                $scope.parentObject = ParentObject;
                scheduleEndpoint = ParentObject.endpoint|| ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;
                $scope.canAdd = false;
                rbacUiControlService.canAdd(scheduleEndpoint)
                    .then(function(canAdd) {
                        $scope.canAdd = canAdd;
                    });
            }

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            $scope.unified_job_options = UnifiedJobsOptions.actions.GET;

            // _.forEach($scope[list.name], buildTooltips);
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

            });
        }

        function buildTooltips(schedule) {
            var job = schedule.summary_fields.unified_job_template;
            if (schedule.enabled) {
                schedule.play_tip = 'Schedule is active. Click to stop.';
                schedule.status = 'active';
                schedule.status_tip = 'Schedule is active. Click to stop.';
            } else {
                schedule.play_tip = 'Schedule is stopped. Click to activate.';
                schedule.status = 'stopped';
                schedule.status_tip = 'Schedule is stopped. Click to activate.';
            }

            schedule.nameTip = schedule.name;
            // include the word schedule if the schedule name does not include the word schedule
            if (schedule.name.indexOf("schedule") === -1 && schedule.name.indexOf("Schedule") === -1) {
                schedule.nameTip += " schedule";
            }
            schedule.nameTip += " for ";
            if (job.name.indexOf("job") === -1 && job.name.indexOf("Job") === -1) {
                schedule.nameTip += "job ";
            }
            schedule.nameTip += job.name;
            schedule.nameTip += ". Click to edit schedule.";
        }

        $scope.refreshSchedules = function() {
            $state.go('.', null, { reload: true });
        };

        $scope.addSchedule = function() {
            $state.go('.add');
        };

        $scope.editSchedule = function(schedule) {
            if ($state.is('jobs.schedules')){
                routeToScheduleForm(schedule, 'edit');
            }
            else {
                $state.go('.edit', { schedule_id: schedule.id });
            }

            function buildStateMap(schedule){

                let deferred = $q.defer();

                switch(schedule.summary_fields.unified_job_template.unified_job_type){
                case 'job':
                    deferred.resolve({
                        name: 'jobTemplateSchedules.edit',
                        params: {
                            id: schedule.unified_job_template,
                            schedule_id: schedule.id
                        }
                    });
                    break;

                    case 'workflow_job':
                        deferred.resolve({
                            name: 'workflowJobTemplateSchedules.edit',
                            params: {
                                id: schedule.unified_job_template,
                                schedule_id: schedule.id
                            }
                        });
                        break;

                    case 'inventory_update':
                        Rest.setUrl(schedule.related.unified_job_template);
                        Rest.get().then( (res) => {
                            deferred.resolve({
                                name: 'inventoryManage.editGroup.schedules.edit',
                                params: {
                                    group_id: res.data.group,
                                    inventory_id: res.data.inventory,
                                    schedule_id: schedule.id,
                                }
                            });
                        });
                        break;

                    case 'project_update':
                        deferred.resolve({
                            name: 'projectSchedules.edit',
                            params: {
                                id: schedule.unified_job_template,
                                schedule_id: schedule.id
                            }
                        });
                        break;

                    case 'system_job':
                        deferred.resolve({
                            name: 'managementJobSchedules.edit',
                            params: {
                                id: schedule.unified_job_template,
                                schedule_id: schedule.id
                            }
                        });
                        break;
                }

                return deferred.promise;
            }

            function routeToScheduleForm(schedule){

                buildStateMap(schedule).then( (state) =>{
                    $state.go(state.name, state.params).catch((err) =>{
                        // stateDefinition.lazyLoad'd state name matcher is not configured to match inventoryManage.* state names
                        // However, the stateDefinition.lazyLoad url matcher will load the correct tree.
                        // Expected error:
                        // Transition rejection error
                        // type: 4  // SUPERSEDED = 2, ABORTED = 3, INVALID = 4, IGNORED = 5, ERROR = 6
                        // detail : "Could not resolve 'inventoryManage.editGroup.schedules.edit' from state 'jobs.schedules'"
                        // message: "This transition is invalid"
                        if (err.type === 4 && err.detail.includes('inventoryManage.editGroup.schedules.edit')){
                            $location.path(`/inventories/${state.params.inventory_id}/manage/edit-group/${state.params.group_id}/schedules/${state.params.schedule_id}`);
                        }
                        else {
                            throw err;
                        }
                    });
                });
            }
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
