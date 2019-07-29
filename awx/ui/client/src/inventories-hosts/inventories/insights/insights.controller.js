/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [ 'InsightsData', '$scope', 'moment', '$state', 'InventoryData',
    'InsightsService', 'CanRemediate', 'InsightsStrings',
function (data, $scope, moment, $state, InventoryData, InsightsService,
    CanRemediate, strings) {

    $scope.strings = strings;

    function init() {
        $scope.reports = (data && data.reports) ? data.reports : [];
        $scope.reports_dataset = (data) ? data : {};
        $scope.currentFilter = "total";
        $scope.solvable_count = filter('solvable').length;
        $scope.not_solvable_count = filter('not_solvable').length;
        $scope.critical_count = filter('critical').length;
        $scope.high_count = filter('high').length;
        $scope.med_count = filter('medium').length;
        $scope.low_count =filter('low').length;
        let a = moment(), b = moment($scope.reports_dataset.last_check_in);
        $scope.last_check_in = a.diff(b, 'hours');
        $scope.inventory = (InventoryData) ? InventoryData : {};
        $scope.insights_credential = (InventoryData && InventoryData.summary_fields &&
            InventoryData.summary_fields.insights_credential && InventoryData.summary_fields.insights_credential.id) ?
                InventoryData.summary_fields.insights_credential.id : null;
        $scope.canRemediate = CanRemediate;
        $scope.platformId = $scope.reports_dataset.platform_id;
    }

    function filter(str){
        return InsightsService.filter(str, $scope.reports_dataset.reports);
    }

    init();

    $scope.filterReports = function(str){
        $scope.currentFilter = str;
        $scope.reports = filter(str);
    };

    $scope.viewDataInInsights = function(){
        window.open(`https://cloud.redhat.com/insights/inventory/${$scope.platformId}/insights`, '_blank');
    };

    $scope.remediateInventory = function(inv_id, insights_credential){
        $state.go('templates.addJobTemplate', {inventory_id: inv_id, credential_id: insights_credential});
    };

    $scope.formCancel = function(){
        $state.go('inventories', null, {reload: true});
    };
}];
