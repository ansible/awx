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
    '$scope', '$location', '$stateParams', 'ScheduleList', 'Rest',
    'rbacUiControlService',
    'ToggleSchedule', 'DeleteSchedule', '$q', '$state', 'Dataset', 'ParentObject', 'UnifiedJobsOptions',
    function($scope, $location, $stateParams,
        ScheduleList, Rest,
        rbacUiControlService,
        ToggleSchedule, DeleteSchedule,
        $q, $state, Dataset, ParentObject, UnifiedJobsOptions) {

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
            if($state.current.name.endsWith('.edit')) {
                $state.go('^.add');
            }
            else if(!$state.current.name.endsWith('.add')) {
                $state.go('.add');
            }
        };

        $scope.editSchedule = function(schedule) {
            if ($state.is('jobs.schedules')){
                routeToScheduleForm(schedule, 'edit');
            }
            else {
                if($state.current.name.endsWith('.add')) {
                    $state.go('^.edit', { schedule_id: schedule.id });
                }
                else if($state.current.name.endsWith('.edit')) {
                    $state.go('.', { schedule_id: schedule.id });
                }
                else {
                    $state.go('.edit', { schedule_id: schedule.id });
                }
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
                                name: 'inventories.edit.inventory_sources.edit.schedules.edit',
                                params: {
                                    inventory_source_id: res.data.id,
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
                            name: 'managementJobsList.schedule.edit',
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
                buildStateMap(schedule).then((state) =>{
                    $state.go(state.name, state.params);
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
