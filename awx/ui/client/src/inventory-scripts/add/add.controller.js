/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'Rest', 'Wait',
    'InventoryScriptsForm', 'ProcessErrors', 'GetBasePath', 'Empty',
    'GenerateForm',  '$scope', '$state', 'Alert',
    function($rootScope, Rest, Wait,
        InventoryScriptsForm, ProcessErrors, GetBasePath, Empty,
        GenerateForm, $scope, $state, Alert
    ) {
        var form = InventoryScriptsForm,
            url = GetBasePath('inventory_scripts');

        init();

        function init() {
            Rest.setUrl(url);
            Rest.options()
                .success(function(data) {
                    if (!data.actions.POST) {
                        $state.go("^");
                        Alert('Permission Error', 'You do not have permission to add an inventory script.', 'alert-info');
                    }
                });

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            // @issue @jmitchell - this setting probably collides with new RBAC can* implementation?
            $scope.canEdit = true;
        }

        // Save
        $scope.formSave = function() {
            Wait('start');
            Rest.setUrl(url);
            Rest.post({
                    name: $scope.name,
                    description: $scope.description,
                    organization: $scope.organization,
                    script: $scope.script
                })
                .success(function(data) {
                    $state.go('inventoryScripts.edit', { inventory_script_id: data.id }, { reload: true });
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new inventory script. POST returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $state.go('^');
        };
    }
];
