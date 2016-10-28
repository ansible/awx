/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'InventoryHosts', 'generateList', 'InventoryManageService', 'HostManageService',
     'hostsUrl', 'SetStatus', 'Prompt', 'Wait', 'inventoryData', '$filter', 'hostsDataset', 'GetBasePath', 'rbacUiControlService',
    function($scope, $rootScope, $state, $stateParams, InventoryHosts, generateList, InventoryManageService, HostManageService,
     hostsUrl, SetStatus, Prompt, Wait, inventoryData, $filter, hostsDataset, GetBasePath, rbacUiControlService){
        var list = InventoryHosts;

        init();
        function init(){
            $scope.inventory_id = $stateParams.inventory_id;

            $scope.canAdd = false;

            rbacUiControlService.canAdd(GetBasePath('inventory') + $scope.inventory_id + "/hosts")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = hostsDataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            // The ncy breadcrumb directive will look at this attribute when attempting to bind to the correct scope.
            // In this case, we don't want to incidentally bind to this scope when editing a host or a group.  See:
            // https://github.com/ncuillery/angular-breadcrumb/issues/42 for a little more information on the
            // problem that this solves.
            $scope.ncyBreadcrumbIgnore = true;
            if($state.current.name === "inventoryManage.editHost") {
                $scope.rowBeingEdited = $state.params.host_id;
                $scope.listBeingEdited = "hosts";
            }
        }

        $scope.createHost = function(){
            $state.go('inventoryManage.addHost');
        };
        $scope.editHost = function(id){
            $state.go('inventoryManage.editHost', {host_id: id});
        };
        $scope.deleteHost = function(id, name){
            var body = '<div class=\"Prompt-bodyQuery\">Are you sure you want to permanently delete the host below from the inventory?</div><div class=\"Prompt-bodyTarget\">' + $filter('sanitize')(name) + '</div>';
            var action = function(){
                delete $rootScope.promptActionBtnClass;
                Wait('start');
                HostManageService.delete(id).then(() => {
                    $('#prompt-modal').modal('hide');
                    if (parseInt($state.params.host_id) === id) {
                        $state.go("inventoryManage", null, {reload: true});
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
        $scope.copyMoveHost = function(id){
            $state.go('inventoryManage.copyMoveHost', {host_id: id});
        };
        $scope.systemTracking = function(){
            var hostIds = _.map($scope.$parent.hostsSelectedItems, (host) => host.id);
            $state.go('systemTracking', {
                inventory: inventoryData,
                inventoryId: $stateParams.inventory_id,
                hosts: $scope.$parent.hostsSelectedItems,
                hostIds: hostIds
            });
        };
        // $scope.$parent governed by InventoryManageController, for unified multiSelect options
        $scope.$on('multiSelectList.selectionChanged', (event, selection) => {
            $scope.$parent.hostsSelected = selection.length > 0 ? true : false;
            $scope.$parent.hostsSelectedItems = selection.selectedItems;
            $scope.$parent.systemTrackingDisabled = selection.length > 0 && selection.length < 3 ? false : true;
            $scope.$parent.systemTrackingTooltip = selection.length > 0 && selection.length < 3 ? "Compare host facts over time" : "Select one or two hosts by clicking the checkbox beside the host. System tracking offers the ability to compare the results of two scan runs from different dates on one host or the same date on two hosts.";
        });
        var cleanUpStateChangeListener = $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
             if (toState.name === "inventoryManage.editHost") {
                 $scope.rowBeingEdited = toParams.host_id;
                 $scope.listBeingEdited = "hosts";
             }
             else {
                 delete $scope.rowBeingEdited;
                 delete $scope.listBeingEdited;
             }
        });
        // Remove the listener when the scope is destroyed to avoid a memory leak
        $scope.$on('$destroy', function() {
            cleanUpStateChangeListener();
        });
    }];
