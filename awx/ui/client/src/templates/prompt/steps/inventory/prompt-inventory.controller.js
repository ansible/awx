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
                    scope.promptData.prompts.inventory.value = row;
                };
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
