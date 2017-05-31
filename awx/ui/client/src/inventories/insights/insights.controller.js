/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [ 'InsightsData', '$scope', 'moment', '$state',
function (data, $scope, moment, $state) {

    function init() {

        $scope.reports = data.reports;
        $scope.reports_dataset = data;
        $scope.currentFilter = "total";
        $scope.solvable_count = _.filter($scope.reports_dataset.reports, (report) => {return report.maintenance_actions.length > 0;}).length;
        $scope.not_solvable_count = _.filter($scope.reports_dataset.reports, (report) => {return report.maintenance_actions.length === 0; }).length;
        $scope.critical_count = 0 || _.filter($scope.reports_dataset.reports, (report) => {return report.rule.severity === "CRITICAL"; }).length;
        $scope.high_count = _.filter($scope.reports_dataset.reports, (report) => {return report.rule.severity === "ERROR"; }).length;
        $scope.med_count = _.filter($scope.reports_dataset.reports, (report) => {return report.rule.severity === "WARN"; }).length;
        $scope.low_count = _.filter($scope.reports_dataset.reports, (report) => {return report.rule.severity === "INFO"; }).length;
        let a = moment(), b = moment($scope.reports_dataset.last_check_in);
        $scope.last_check_in = a.diff(b, 'hours');
    }

    init();

    $scope.filter = function(filter){
        $scope.currentFilter = filter;
        if(filter === "total"){
            $scope.reports = $scope.reports_dataset.reports;
        }
        if(filter === "solvable"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.maintenance_actions.length > 0){
                    return report;
                }
            });
        }
        if(filter === "not_solvable"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.maintenance_actions.length === 0){
                    return report;
                }
            });
        }
        if(filter === "critical"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.rule.severity === 'CRITICAL'){
                    return report;
                }
            });
        }
        if(filter === "high"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.rule.severity === 'ERROR'){
                    return report;
                }
            });
        }
        if(filter === "medium"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.rule.severity === 'WARN'){
                    return report;
                }
            });
        }
        if(filter === "low"){
            $scope.reports = _.filter($scope.reports_dataset.reports, function(report){
                if(report.rule.severity === 'INFO'){
                    return report;
                }
            });
        }
    };
    $scope.viewDataInInsights = function(){
        window.open(`https://access.redhat.com/insights/inventory?machine=${$scope.$parent.host.insights_system_id}`, '_blank');
    };
    $scope.remediateInventory = function(){
        $state.go('templates.addJobTemplate');
    };
    $scope.formCancel = function(){
        $state.go('inventories', null, {reload: true});
    };
}];
