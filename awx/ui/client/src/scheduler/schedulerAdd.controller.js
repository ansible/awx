/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$compile', '$filter', '$state', '$stateParams', 'AddSchedule', 'Wait',
    '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'GetBasePath',
    'Rest', 'ParamPass',
    function($compile, $filter, $state, $stateParams, AddSchedule, Wait, $scope,
        $rootScope, CreateSelect2, ParseTypeChange, GetBasePath, Rest, ParamPass) {

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

    var schedule_url = ParamPass.get();

    $scope.formCancel = function() {
        $state.go("^");
    };

    // extra_data field is not manifested in the UI when scheduling a Management Job
    if ($state.current.name === 'jobTemplateSchedules.add'){
        $scope.parseType = 'yaml';
        // grab any existing extra_vars from parent job_template
        var defaultUrl = GetBasePath('job_templates') + $stateParams.id + '/';
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
        $scope.extraVars = '---';
        $scope.parseType = 'yaml';
        ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
    }
    else if ($state.current.name === 'inventoryManage.schedules.add'){
        $scope.extraVars = '---';
        $scope.parseType = 'yaml';
        ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
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
