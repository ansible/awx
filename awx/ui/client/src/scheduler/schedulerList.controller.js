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
    'Find', 'ToggleSchedule', 'DeleteSchedule', 'GetChoices', '$q', '$state', 'Dataset', 'ParentObject',
    function($scope, $compile, $location, $stateParams,
        SchedulesList, Rest, ProcessErrors, ReturnToCaller, ClearScope,
        GetBasePath, Wait, rbacUiControlService, Find,
        ToggleSchedule, DeleteSchedule, GetChoices,
        $q, $state, Dataset, ParentObject) {

        ClearScope();

        var base, scheduleEndpoint,
            list = SchedulesList;

        init();

        function init() {
            if (ParentObject){
                $scope.parentObject = ParentObject;
                scheduleEndpoint = ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;
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

            _.forEach($scope[list.name], buildTooltips);
        }

        function buildTooltips(schedule) {
            if (schedule.enabled) {
                schedule.play_tip = 'Schedule is active. Click to stop.';
                schedule.status = 'active';
                schedule.status_tip = 'Schedule is active. Click to stop.';
            } else {
                schedule.play_tip = 'Schedule is stopped. Click to activate.';
                schedule.status = 'stopped';
                schedule.status_tip = 'Schedule is stopped. Click to activate.';
            }
        }

        $scope.refreshSchedules = function() {
            $state.go('.', null, { reload: true });
        };

        $scope.addSchedule = function() {
            $state.go('.add');
        };

        $scope.editSchedule = function(schedule_id) {
            $state.go('.edit', { schedule_id: schedule_id });
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
        console.log(base)
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

        // @issue - believe this is no longer necessary now that parent object is resolved prior to controller initilizing

        // Wait('start');

        // GetChoices({
        //     scope: $scope,
        //     url: GetBasePath('unified_jobs'),   //'/static/sample/data/types/data.json'
        //     field: 'type',
        //     variable: 'type_choices',
        //     callback: 'choicesReady'
        // });
    }
];
