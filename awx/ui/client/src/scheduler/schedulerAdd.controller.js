/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$compile', '$state', '$stateParams', 'AddSchedule', 'Wait',
    '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'GetBasePath',
    'Rest', 'ParamPass',
    function($compile, $state, $stateParams, AddSchedule, Wait, $scope,
        $rootScope, CreateSelect2, ParseTypeChange, GetBasePath, Rest, ParamPass) {

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
            "schedulerEndDt"
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
        var defaultUrl = GetBasePath('job_templates') + $stateParams.id + '/';
        Rest.setUrl(defaultUrl);
        Rest.get().then(function(res){
            // sanitize
            var data = JSON.parse(JSON.stringify(res.data.extra_vars));
            $scope.extraVars = data === '' ? '---' :  data;
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        });
        $scope.$watch('extraVars', function(){
            if ($scope.parseType === 'yaml'){
                try{
                    $scope.serializedExtraVars = jsyaml.safeLoad($scope.extraVars);
                }
                catch(err){ return; }
            }
            else if ($scope.parseType === 'json'){
                try{
                    $scope.serializedExtraVars = JSON.parse($scope.extraVars);
                }
                catch(err){ return; }
            }
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
    else if ($state.current.name === 'inventoryManageSchedules.add'){
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
