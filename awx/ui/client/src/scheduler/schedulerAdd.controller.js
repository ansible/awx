export default ['$compile', '$state', '$stateParams', 'AddSchedule', 'Wait', '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'JobTemplateExtraVars', function($compile, $state, $stateParams, AddSchedule, Wait, $scope, $rootScope, CreateSelect2, ParseTypeChange, JobTemplateExtraVars) {
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


    $scope.formCancel = function() {
        $state.go("^");
    };

    // extra_data field is not manifested in the UI when scheduling a Management Job
    if ($state.current.name !== ('managementJobSchedules.add' || 'managementJobSchedules.edit')){
        $scope.parseType = 'yaml';
        $scope.extraVars = JobTemplateExtraVars === '' || JobTemplateExtraVars === null  ? '---' :  JobTemplateExtraVars;
        ParseTypeChange({ 
            scope: $scope, 
            variable: 'extraVars', 
            parse_variable: 'parseType',
            field_id: 'SchedulerForm-extraVars' 
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


    AddSchedule({
        scope: $scope,
        callback: 'SchedulesRefresh',
        base: $scope.base ? $scope.base : null
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
