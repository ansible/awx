/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait',
    'InventoryScriptsForm', 'ProcessErrors', 'GetBasePath',
    'GenerateForm', 'inventory_scriptData',
    '$scope', '$state',
    function(
        Rest, Wait, InventoryScriptsForm, ProcessErrors, GetBasePath,
        GenerateForm, inventory_scriptData,
        $scope, $state
    ) {
        var generator = GenerateForm,
            data = inventory_scriptData,
            id = inventory_scriptData.id,
            form = InventoryScriptsForm,
            main = {},
            url = GetBasePath('inventory_scripts');

        init();

        function init() {
            $scope.inventory_script = inventory_scriptData;

            $scope.$watch('inventory_script_obj.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAdd = false;
                }
            });

            var fld;
            for (fld in form.fields) {
                if (data[fld]) {
                    $scope[fld] = data[fld];
                    main[fld] = data[fld];
                }

                if (form.fields[fld].sourceModel && data.summary_fields &&
                    data.summary_fields[form.fields[fld].sourceModel]) {
                    $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    main[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                }
            }

        }

        $scope.formSave = function() {
            generator.clearApiErrors($scope);
            Wait('start');
            Rest.setUrl(url + id + '/');
            Rest.put({
                    name: $scope.name,
                    description: $scope.description,
                    organization: $scope.organization,
                    script: $scope.script
                })
                .then(() => {
                    $state.go('inventoryScripts', null, { reload: true });
                    Wait('stop');
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new inventory script. PUT returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $state.go('inventoryScripts');
        };

    }
];
