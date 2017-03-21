/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobSubInvListController from './job-sub-inv-list.controller';

export default [ 'templateUrl', 'QuerySet', 'GetBasePath', 'generateList', '$compile', 'InventoryList',
    (templateUrl, qs, GetBasePath, GenerateList, $compile, InventoryList) => {
    return {
        scope: {
          selectedInventory: '='
        },
        templateUrl: templateUrl('job-submission/lists/inventory/job-sub-inv-list'),
        controller: jobSubInvListController,
        restrict: 'E',
        link: scope => {
            let toDestroy = [];

            scope.inventory_default_params = {
                order_by: 'name',
                page_size: 5
            };

            scope.inventory_queryset = {
                order_by: 'name',
                page_size: 5
            };

            // Fire off the initial search
            qs.search(GetBasePath('inventory'), scope.inventory_default_params)
                .then(res => {
                    scope.inventory_dataset = res.data;
                    scope.inventories = scope.inventory_dataset.results;

                    let invList = _.cloneDeep(InventoryList);
                    let html = GenerateList.build({
                        list: invList,
                        input_type: 'radio',
                        mode: 'lookup'
                    });

                    scope.list = invList;

                    $('#job-submission-inventory-lookup').append($compile(html)(scope));

                    toDestroy.push(scope.$watchCollection('selectedInventory', () => {
                        if(scope.selectedInventory) {
                            // Loop across the inventories and see if one of them should be "checked"
                            scope.inventories.forEach((row, i) => {
                                if (row.id === scope.selectedInventory.id) {
                                    scope.inventories[i].checked = 1;
                                }
                                else {
                                    scope.inventories[i].checked = 0;
                                }
                            });
                        }
                    }));
                });

            scope.$on('$destroy', () => toDestroy.forEach(watcher => watcher()));
        }
    };
}];
