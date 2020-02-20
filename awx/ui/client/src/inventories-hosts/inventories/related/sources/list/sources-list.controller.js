/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'SourcesListDefinition',
    'InventoryUpdate', 'CancelSourceUpdate',
    'ViewUpdateStatus', 'rbacUiControlService', 'GetBasePath',
    'GetSyncStatusMsg', 'Dataset', 'Find', 'QuerySet',
    'inventoryData', '$filter', 'Prompt', 'Wait', 'SourcesService', 'inventorySourceOptions',
    'canAdd', 'hasSyncableSources', 'i18n', 'InventoryHostsStrings', 'InventorySourceModel', 'ProcessErrors',
    function($scope, $rootScope, $state, $stateParams, SourcesListDefinition,
        InventoryUpdate, CancelSourceUpdate,
        ViewUpdateStatus, rbacUiControlService, GetBasePath, GetSyncStatusMsg,
        Dataset, Find, qs, inventoryData, $filter, Prompt,
        Wait, SourcesService, inventorySourceOptions, canAdd, hasSyncableSources, i18n,
             InventoryHostsStrings, InventorySource, ProcessErrors){

        let inventorySource = new InventorySource();

        let list = SourcesListDefinition;
        var inventory_source;

        init();

        function init(){
            $scope.inventory_id = $stateParams.inventory_id;
            $scope.canAdhoc = inventoryData.summary_fields.user_capabilities.adhoc;
            $scope.canAdd = canAdd;
            $scope.showSyncAll = hasSyncableSources;

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.inventory_id = $stateParams.inventory_id;
            _.forEach($scope[list.name], buildStatusIndicators);
            optionsRequestDataProcessing();

            $scope.$on(`ws-jobs`, function(e, data){
                inventory_source = Find({ list: $scope.inventory_sources, key: 'id', val: data.inventory_source_id });

                if (inventory_source) {
                    var status = GetSyncStatusMsg({
                        status: data.status
                    });
                    inventory_source.status = data.status;
                    inventory_source.status_class = status.class;
                    inventory_source.status_tooltip = status.tooltip;
                    inventory_source.launch_tooltip = status.launch_tip;
                    inventory_source.launch_class = status.launch_class;
                }
            });

            $scope.$watchCollection(`${$scope.list.name}`, function() {
                _.forEach($scope[list.name], buildStatusIndicators);
                optionsRequestDataProcessing();
            });
        }

        function optionsRequestDataProcessing(){
            if ($scope[list.name] !== undefined) {
                $scope[list.name].forEach(function(item, item_idx) {
                    var itm = $scope[list.name][item_idx];

                    // Set the item source label
                    if (list.fields.source && inventorySourceOptions && inventorySourceOptions.hasOwnProperty('source')) {
                            inventorySourceOptions.source.choices.forEach(function(choice) {
                                if (choice[0] === item.source) {
                                itm.source_label = choice[1];
                            }
                        });
                    }
                });
            }
        }

        function buildStatusIndicators(inventory_source){
            if (inventory_source === undefined || inventory_source === null) {
                inventory_source = {};
            }

            let inventory_source_status;

            inventory_source_status = GetSyncStatusMsg({
                status: inventory_source.status,
                has_inventory_sources: inventory_source.has_inventory_sources,
                source: ( (inventory_source) ? inventory_source.source : null )
            });
            _.assign(inventory_source,
                {status_class: inventory_source_status.class},
                {status_tooltip: inventory_source_status.tooltip},
                {launch_tooltip: inventory_source_status.launch_tip},
                {launch_class: inventory_source_status.launch_class},
                {source: inventory_source ? inventory_source.source : null},
                {status: inventory_source ? inventory_source.status : null});
        }

        $scope.createSource = function(){
            $state.go('inventories.edit.inventory_sources.add');
        };
        $scope.editSource = function(id){
            $state.go('inventories.edit.inventory_sources.edit', {inventory_source_id: id});
        };
        $scope.deleteSource = function(inventory_source){
            var action = function(){
                $rootScope.promptActionBtnClass = "Modal-errorButton--sourcesDelete";
                Wait('start');
                let hostDelete = SourcesService.deleteHosts(inventory_source.id).catch(({data, status}) => {
                    $('#prompt-modal').modal('hide');
                    Wait('stop');
                    ProcessErrors($scope, data, status, null,
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('There was an error deleting inventory source hosts. Returned status: ') +
                                status
                        });
                });
                let groupDelete = SourcesService.deleteGroups(inventory_source.id).catch(({data, status}) => {
                    $('#prompt-modal').modal('hide');
                    Wait('stop');
                    ProcessErrors($scope, data, status, null,
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('There was an error deleting inventory source groups. Returned status: ') +
                                status
                        });
                });
                Promise.all([hostDelete, groupDelete]).then(() => {
                        SourcesService.delete(inventory_source.id).then(() => {
                            $('#prompt-modal').modal('hide');
                            delete $rootScope.promptActionBtnClass;
                            let reloadListStateParams = null;

                            if($scope.inventory_sources.length === 1 && $state.params.inventory_source_search && !_.isEmpty($state.params.inventory_source_search.page) && $state.params.inventory_source_search.page !== '1') {
                                reloadListStateParams = _.cloneDeep($state.params);
                                reloadListStateParams.inventory_source_search.page = (parseInt(reloadListStateParams.inventory_source_search.page)-1).toString();
                            }
                            if (parseInt($state.params.inventory_source_id) === inventory_source.id) {
                                $state.go('^', reloadListStateParams, {reload: true});
                            } else {
                                $state.go('.', reloadListStateParams, {reload: true});
                            }
                            Wait('stop');
                        })
                        .catch(({data, status}) => {
                            $('#prompt-modal').modal('hide');
                            Wait('stop');
                            ProcessErrors($scope, data, status, null,
                                {
                                    hdr: i18n._('Error!'),
                                    msg: i18n._('There was an error deleting inventory source. Returned status: ') +
                                        status
                                });
                        });
                    });
            };

            inventorySource.getDependentResourceCounts(inventory_source.id)
                .then((counts) => {
                    const invalidateRelatedLines = [];
                    let deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryHostsStrings.get('deleteResource.CONFIRM', 'inventory source')}</div>`;

                    counts.forEach(countObj => {
                        if(countObj.count && countObj.count > 0) {
                            invalidateRelatedLines.push(`<div><span class="Prompt-warningResourceTitle">${countObj.label}</span><span class="badge List-titleBadge">${countObj.count}</span></div>`);
                        }
                    });

                    if (invalidateRelatedLines && invalidateRelatedLines.length > 0) {
                        deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryHostsStrings.get('deleteResource.USED_BY', 'inventory source')} ${InventoryHostsStrings.get('deleteResource.CONFIRM', 'inventory source')}</div>`;
                        invalidateRelatedLines.forEach(invalidateRelatedLine => {
                            deleteModalBody += invalidateRelatedLine;
                        });
                    }

                    Prompt({
                        hdr: i18n._('Delete Source'),
                        resourceName: $filter('sanitize')(inventory_source.name),
                        body: deleteModalBody,
                        action: action,
                        actionText: i18n._('DELETE')
                    });
                    $rootScope.promptActionBtnClass = 'Modal-errorButton';
                });

        };

        $scope.updateSource = function(inventory_source) {
            InventoryUpdate({
                scope: $scope,
                url: inventory_source.related.update
            });
        };

        $scope.cancelUpdate = function (id) {
            CancelSourceUpdate({ scope: $scope, id: id });
        };

        $scope.viewUpdateStatus = function (id) {
            ViewUpdateStatus({
                scope: $scope,
                inventory_source_id: id
            });
        };

        $scope.syncAllSources = function() {
            InventoryUpdate({
                scope: $scope,
                url: inventoryData.related.update_inventory_sources,
                updateAllSources: true
            });
        };

    }];
