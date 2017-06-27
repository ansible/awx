/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


function HostsList($scope, HostsList, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostsService, SetStatus, canAdd) {

    let list = HostsList;

    init();

    function init(){
        $scope.canAdd = canAdd;
        $scope.enableSmartInventoryButton = false;

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $rootScope.flashMessage = null;

        $scope.$watchCollection(list.name, function() {
            $scope[list.name] = _.map($scope.hosts, function(value) {
                value.inventory_name = value.summary_fields.inventory.name;
                value.inventory_id = value.summary_fields.inventory.id;
                return value;
            });
            setJobStatus();
        });

        $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
            if(toParams && toParams.host_search) {
                let hasMoreThanDefaultKeys = false;
                angular.forEach(toParams.host_search, function(value, key) {
                    if(key !== 'order_by' && key !== 'page_size') {
                        hasMoreThanDefaultKeys = true;
                    }
                });
                $scope.enableSmartInventoryButton = hasMoreThanDefaultKeys ? true : false;
            }
            else {
                $scope.enableSmartInventoryButton = false;
            }
        });

    }

    function setJobStatus(){
        _.forEach($scope.hosts, function(value) {
            SetStatus({
                scope: $scope,
                host: value
            });
        });
    }

    $scope.createHost = function(){
        $state.go('hosts.add');
    };
    $scope.editHost = function(id){
        $state.go('hosts.edit', {host_id: id});
    };
    $scope.goToInsights = function(id){
        $state.go('hosts.edit.insights', {host_id:id});
    };
    $scope.toggleHost = function(event, host) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }

        host.enabled = !host.enabled;

        HostsService.put(host).then(function(){
            $state.go($state.current, null, {reload: true});
        });
    };

    $scope.smartInventory = function() {
        // Gather up search terms and pass them to the add smart inventory form
        let stateParamsCopy = angular.copy($state.params.host_search);
        let defaults = _.find($state.$current.path, (step) => {
            if(step && step.params && step.params.hasOwnProperty(`host_search`)){
                return step.params.hasOwnProperty(`host_search`);
            }
        }).params[`host_search`].config.value;

        // Strip defaults out of the state params copy
        angular.forEach(Object.keys(defaults), function(value) {
            delete stateParamsCopy[value];
        });

        $state.go('inventories.addSmartInventory', {hostfilter: JSON.stringify(stateParamsCopy)});
    };

    $scope.editInventory = function(host) {
        if(host.summary_fields && host.summary_fields.inventory) {
            if(host.summary_fields.inventory.kind && host.summary_fields.inventory.kind === 'smart') {
                $state.go('inventories.editSmartInventory', {smartinventory_id: host.inventory});
            }
            else {
                $state.go('inventories.edit', {inventory_id: host.inventory});
            }
        }
    };

}

export default ['$scope', 'HostsList', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait',
    'HostsService', 'SetStatus', 'canAdd', HostsList
];
