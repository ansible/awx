export default ['$compile', '$state', '$stateParams', 'EditSchedule', 'Wait', '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', function($compile, $state, $stateParams, EditSchedule, Wait, $scope, $rootScope, CreateSelect2, ParseTypeChange) {
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

        $rootScope.$broadcast("loadSchedulerDetailPane");
        Wait('stop');
    });

    $scope.isEdit = true;
    $scope.hideForm = true;
    $scope.parseType = 'yaml';

    $scope.formCancel = function() {
        $state.go("^");
    };

    // extra_data field is not manifested in the UI when scheduling a Management Job
    if ($state.current.name !== 'managementJobSchedules.add' && $state.current.name !== 'managementJobSchedules.edit'){
        $scope.$on('ScheduleFound', function(){
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        });
    }

    EditSchedule({
        scope: $scope,
        id: parseInt($stateParams.schedule_id),
        callback: 'SchedulesRefresh',
        base: $scope.base ? $scope.base: null
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
