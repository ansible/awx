/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptInventoryController from './prompt-inventory.controller';

export default [ 'templateUrl', 'QuerySet', 'GetBasePath', 'generateList', '$compile', 'InventoryList', 'i18n',
    (templateUrl, qs, GetBasePath, GenerateList, $compile, InventoryList, i18n) => {
    return {
        scope: {
            promptData: '=',
            readOnlyPrompts: '<'
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
                    invList.disableRow = "{{ readOnlyPrompts }}";
                    invList.disableRowValue = "readOnlyPrompts";

                    const listConfig = {
                        list: invList,
                        input_type: 'radio',
                        mode: 'lookup',
                    };

                    if (scope.promptData.templateType === "workflow_job_template") {
                        listConfig.lookupMessage = i18n._("This inventory is applied to all job templates nodes that prompt for an inventory.");
                    }

                    let html = GenerateList.build(listConfig);

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
