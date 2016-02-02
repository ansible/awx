export default ['$compile', '$state', '$stateParams', 'AddSchedule', 'Wait', '$scope', function($compile, $state, $stateParams, AddSchedule, Wait, $scope) {
    $scope.$on("ScheduleFormCreated", function(e, scope) {
        $scope.hideForm = false;
        $scope = angular.extend($scope, scope);
        $scope.$watchGroup(["schedulerStartDt",
            "schedulerStartHour",
            "schedulerStartMinute",
            "schedulerStartSecond",
            "schedulerTimeZone",
            "schedulerFrequency",
            "schedulerInterval"], function(val) {
                if (!$scope.scheduler_form.$invalid) {
                    $scope.schedulerIsValid = true;
                } else {
                    $scope.schedulerIsValid = false;
                }
                return val;
        });
        Wait('stop');
    });

    $scope.hideForm = true;

    $scope.formCancel = function() {
        $state.go("^");
    }

    AddSchedule({
        scope: $scope,
        callback: 'SchedulesRefresh'
    });
}];
