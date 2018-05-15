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
    'rbacUiControlService',
    'ToggleSchedule', 'DeleteSchedule', '$q', '$state', 'Dataset', 'ParentObject', 'UnifiedJobsOptions',
    function($filter, $scope, $location, $stateParams,
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

                if (!$state.is('jobs.schedules')){
                    if($state.current.name.endsWith('.add')) {
                        itm.linkToDetails = `^.edit({schedule_id:schedule.id})`;
                    }
                    else if($state.current.name.endsWith('.edit')) {
                        itm.linkToDetails = `.({schedule_id:schedule.id})`;
                    }
                    else {
                        itm.linkToDetails = `.edit({schedule_id:schedule.id})`;
                    }
                }

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
            schedule.nameTip += ". Click to edit schedule.";
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
            if ($state.is('jobs.schedules')){
                $state.go('jobs.schedules.edit', {schedule_id: schedule.id});
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
