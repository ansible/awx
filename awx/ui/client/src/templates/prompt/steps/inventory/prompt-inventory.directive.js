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

                    const defaultWarning = i18n._("This inventory is applied to all job template nodes that prompt for an inventory.");
                    const missingWarning = i18n._("This workflow job template has a default inventory which must be included or replaced before proceeding.");

                    const updateInventoryWarning = () => {
                        scope.inventoryWarning = null;
                        if (scope.promptData.templateType === "workflow_job_template") {
                            scope.inventoryWarning = defaultWarning;

                            const isPrompted = _.get(scope.promptData, 'launchConf.ask_inventory_on_launch');
                            const isDefault =  _.get(scope.promptData, 'launchConf.defaults.inventory.id');
                            const isSelected = _.get(scope.promptData, 'prompts.inventory.value.id', null) !== null;

                            if (isPrompted && isDefault && !isSelected) {
                                scope.inventoryWarning = missingWarning;
                            }
                        }
                    };

                    updateInventoryWarning();

                    let html = GenerateList.build({
                        list: invList,
                        input_type: 'radio',
                        mode: 'lookup',
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

                            updateInventoryWarning();
                        });
                    });
                });
        }
    };
}];
