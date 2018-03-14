/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptInventoryController from './prompt-inventory.controller';

export default [ 'templateUrl', 'QuerySet', 'GetBasePath', 'generateList', '$compile', 'InventoryList',
    (templateUrl, qs, GetBasePath, GenerateList, $compile, InventoryList) => {
    return {
        scope: {
            promptData: '='
        },
        templateUrl: templateUrl('templates/prompt/steps/inventory/prompt-inventory'),
        controller: promptInventoryController,
        controllerAs: 'vm',
        require: ['^^prompt', 'promptInventory'],
        restrict: 'E',
        replace: true,
        transclude: true,
        link: (scope, el, attrs, controllers) => {

            const launchController = controllers[0];
            const promptInventoryController = controllers[1];

            promptInventoryController.init(scope, launchController);

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

                    $('#prompt-inventory').append($compile(html)(scope));

                    scope.$watch('promptData.prompts.inventory.value', () => {
                        scope.inventories.forEach((row, i) => {
                            if (
                                _.has(scope, 'promptData.prompts.inventory.value.id') &&
                                row.id === scope.promptData.prompts.inventory.value.id
                            ) {
                                scope.inventories[i].checked = 1;
                            }
                            else {
                                scope.inventories[i].checked = 0;
                            }
                        });
                    });
                });
        }
    };
}];
