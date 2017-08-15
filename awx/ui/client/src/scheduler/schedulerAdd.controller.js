/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$filter', '$state', '$stateParams', 'AddSchedule', 'Wait',
    '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'GetBasePath',
    'Rest', 'ParentObject',
    function($filter, $state, $stateParams, AddSchedule, Wait, $scope,
        $rootScope, CreateSelect2, ParseTypeChange, GetBasePath, Rest, ParentObject) {
    $scope.processSchedulerEndDt = function(){
        // set the schedulerEndDt to be equal to schedulerStartDt + 1 day @ midnight
        var dt = new Date($scope.schedulerUTCTime);
        // increment date by 1 day
        dt.setDate(dt.getDate() + 1);
        var month = $filter('schZeroPad')(dt.getMonth() + 1, 2),
            day = $filter('schZeroPad')(dt.getDate(), 2);
        $scope.$parent.schedulerEndDt = month + '/' + day + '/' + dt.getFullYear();
    };

    // initial end @ midnight values
    $scope.schedulerEndHour = "00";
    $scope.schedulerEndMinute = "00";
    $scope.schedulerEndSecond = "00";
    $scope.parentObject = ParentObject;

    /*
     * This is a workaround for the angular-scheduler library inserting `ll` into fields after an
     * invalid entry and never unsetting them. Presumably null is being truncated down to 2 chars 
     * in that case.
     *
     * Because this same problem exists in the edit mode and because there's no inheritence, this
     * block of code is duplicated in both add/edit controllers pending a much needed broader
     * refactoring effort.
     */
    $scope.timeChange = () => {
        if (!Number($scope.schedulerStartHour)) {
            $scope.schedulerStartHour = '00';
        }

        if (!Number($scope.schedulerStartMinute)) {
            $scope.schedulerStartMinute = '00';
        }

        if (!Number($scope.schedulerStartSecond)) {
            $scope.schedulerStartSecond = '00';
        }

        $scope.scheduleTimeChange();
    };

    $scope.$on("ScheduleFormCreated", function(e, scope) {
        $scope.hideForm = false;
        $scope = angular.extend($scope, scope);
        $scope.$on("formUpdated", function() {
            $rootScope.$broadcast("loadSchedulerDetailPane");
        });

        $scope.$watchGroup(["schedulerName",
            "schedulerStartDt",
            "schedulerStartHour",
            "schedulerStartMinute",
            "schedulerStartSecond",
            "schedulerTimeZone",
            "schedulerFrequency",
            "schedulerInterval",
            "monthlyRepeatOption",
            "monthDay",
            "monthlyOccurrence",
            "monthlyWeekDay",
            "yearlyRepeatOption",
            "yearlyMonth",
            "yearlyMonthDay",
            "yearlyOccurrence",
            "yearlyWeekDay",
            "yearlyOtherMonth",
            "schedulerEnd",
            "schedulerOccurrenceCount",
            "schedulerEndDt",
            "schedulerEndHour",
            "schedulerEndMinute",
            "schedularEndSecond"
        ], function() {
            $scope.$emit("formUpdated");
        }, true);

        $scope.$watch("weekDays", function() {
            $scope.$emit("formUpdated");
        }, true);

        Wait('stop');
    });

    $scope.hideForm = true;

    var schedule_url = ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;

    $scope.formCancel = function() {
        $state.go("^");
    };

    // extra_data field is not manifested in the UI when scheduling a Management Job
    if ($state.current.name === 'jobTemplateSchedules.add'){
        $scope.parseType = 'yaml';
        // grab any existing extra_vars from parent job_template
        let defaultUrl = GetBasePath('job_templates') + $stateParams.id + '/';
        Rest.setUrl(defaultUrl);
        Rest.get().then(function(res){
            var data = res.data.extra_vars;
            $scope.extraVars = data === '' ? '---' :  data;
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        });
    }
    else if ($state.current.name === 'workflowJobTemplateSchedules.add'){
        $scope.parseType = 'yaml';
        // grab any existing extra_vars from parent workflow_job_template
        let defaultUrl = GetBasePath('workflow_job_templates') + $stateParams.id + '/';
        Rest.setUrl(defaultUrl);
        Rest.get().then(function(res){
            var data = res.data.extra_vars;
            $scope.extraVars = data === '' ? '---' :  data;
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        });
    }
    else if ($state.current.name === 'projectSchedules.add'){
        $scope.noVars = true;
    }
    else if ($state.current.name === 'inventories.edit.inventory_sources.edit.schedules.add'){
        $scope.noVars = true;
    }
    AddSchedule({
        scope: $scope,
        callback: 'SchedulesRefresh',
        base: $scope.base ? $scope.base : null,
        url: schedule_url
    });

    var callSelect2 = function() {
        CreateSelect2({
            element: '.MakeSelect2',
            multiple: false
        });
    };

    $scope.$on("updateSchedulerSelects", function() {
        callSelect2();
    });

    callSelect2();

}];
