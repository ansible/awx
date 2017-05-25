/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


function HostsList($scope, HostsList, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostManageService, SetStatus, canAdd) {

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
    $scope.deleteHost = function(id, name){
        var body = '<div class=\"Prompt-bodyQuery\">Are you sure you want to permanently delete the host below from the inventory?</div><div class=\"Prompt-bodyTarget\">' + $filter('sanitize')(name) + '</div>';
        var action = function(){
            delete $rootScope.promptActionBtnClass;
            Wait('start');
            HostManageService.delete(id).then(() => {
                $('#prompt-modal').modal('hide');
                if (parseInt($state.params.host_id) === id) {
                    $state.go("hosts", null, {reload: true});
                } else {
                    $state.go($state.current.name, null, {reload: true});
                }
                Wait('stop');
            });
        };
        // Prompt depends on having $rootScope.promptActionBtnClass available...
        Prompt({
            hdr: 'Delete Host',
            body: body,
            action: action,
            actionText: 'DELETE',
        });
        $rootScope.promptActionBtnClass = 'Modal-errorButton';
    };

    $scope.toggleHost = function(event, host) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }

        host.enabled = !host.enabled;

        HostManageService.put(host).then(function(){
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
    'HostManageService', 'SetStatus', 'canAdd', HostsList
];
