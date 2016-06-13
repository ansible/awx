/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'InventoryHosts', 'generateList', 'InventoryManageService', 'HostManageService',
     'hostsUrl', 'SearchInit', 'PaginateInit', 'SetStatus', 'Prompt', 'Wait', 'inventoryData',
    function($scope, $rootScope, $state, $stateParams, InventoryHosts, generateList, InventoryManageService, HostManageService,
     hostsUrl, SearchInit, PaginateInit, SetStatus, Prompt, Wait, inventoryData){
        var list = InventoryHosts,
            view = generateList,
            pageSize = 20;
        $scope.createHost = function(){
            $state.go('inventoryManage.addHost');
        };
        $scope.editHost = function(id){
            $state.go('inventoryManage.editHost', {host_id: id});
        };
        $scope.deleteHost = function(id, name){
            var body = '<div class=\"Prompt-bodyQuery\">Are you sure you want to permanently delete the host below from the inventory?</div><div class=\"Prompt-bodyTarget\">' + name + '</div>';
            var action = function(){
                delete $rootScope.promptActionBtnClass;
                Wait('start');
                HostManageService.delete(id).then(() => {
                    $('#prompt-modal').modal('hide');
                    $state.go($state.current.name, null, {reload: true});
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
            $scope.$parent.systemTrackingTooltip = selection.length === 1 ? "Compare host facts over time" : "Compare hosts' facts";
        });
        $scope.$on('PostRefresh', ()=>{
            _.forEach($scope.hosts, (host) => SetStatus({scope: $scope, host: host}));
        });
        var init = function(){
            list.basePath = hostsUrl;
            view.inject(list,{
                id: 'hosts-list',
                scope: $scope,
                mode: 'edit'
            });
            SearchInit({
                scope: $scope,
                list: list,
                url: hostsUrl,
                set: 'hosts'
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: hostsUrl,
                pageSize: pageSize
            });
            $scope.search(list.iterator);
        };
        init();
    }];