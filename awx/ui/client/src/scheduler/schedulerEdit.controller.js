export default ['$compile', '$state', '$stateParams', 'EditSchedule', 'Wait', '$scope', '$rootScope', 'CreateSelect2', function($compile, $state, $stateParams, EditSchedule, Wait, $scope, $rootScope, CreateSelect2) {
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

    $scope.formCancel = function() {
        $state.go("^");
    }

    EditSchedule({
        scope: $scope,
        id: parseInt($stateParams.schedule_id),
        callback: 'SchedulesRefresh'
    });

    var callSelect2 = function() {
        CreateSelect2({
            element: '#schedulerTimeZone',
            multiple: false
        });

        CreateSelect2({
            element: '#schedulerFrequency',
            multiple: false
        });

        CreateSelect2({
            element: '#monthlyWeekDay',
            multiple: false
        });

        CreateSelect2({
            element: '#monthlyOccurrence',
            multiple: false
        });

        CreateSelect2({
            element: '#monthlyOccurrence',
            multiple: false
        });

        CreateSelect2({
            element: '#yearlyMonth',
            multiple: false
        });

        CreateSelect2({
            element: '#yearlyWeekDay',
            multiple: false
        });

        CreateSelect2({
            element: '#yearlyOccurrence',
            multiple: false
        });

        CreateSelect2({
            element: '#yearlyOtherMonth',
            multiple: false
        });

        CreateSelect2({
            element: '#schedulerEnd',
            multiple: false
        });
    };

    $scope.$on("updateSchedulerSelects", function() {
        callSelect2();
        console.log("select2 is called");
    });

    callSelect2();
}];
