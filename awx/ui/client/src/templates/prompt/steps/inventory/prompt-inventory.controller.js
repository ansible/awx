/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [ 'TemplatesStrings', function(strings) {
            const vm = this;

            vm.strings = strings;

            let scope;
            let launch;

            vm.init = (_scope_, _launch_) => {
                scope = _scope_;
                launch = _launch_;

                scope.toggle_row = (row) => {
                    if (!scope.readOnlyPrompts) {
                        scope.promptData.prompts.inventory.value = row;
                    }
                };

                scope.$watchCollection('inventories', () => {
                    if(scope.inventories && scope.inventories.length > 0) {
                        scope.inventories.forEach((credential, i) => {
                            if (_.has(scope, 'promptData.prompts.inventory.value.id') && scope.promptData.prompts.inventory.value.id === scope.inventories[i].id) {
                                scope.inventories[i].checked = 1;
                            } else {
                                scope.inventories[i].checked = 0;
                            }

                        });
                    }
                });
            };

            vm.deleteSelectedInventory = () => {
                scope.promptData.prompts.inventory.value = null;

                scope.inventories.forEach((inventory) => {
                    inventory.checked = 0;
                });
            };

            vm.revert = () => {
                scope.promptData.prompts.inventory.value = scope.promptData.launchConf.defaults.inventory;
            };
        }
    ];
