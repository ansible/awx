/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'Rest', 'Wait',
        'inventoryScriptsFormObject', 'ProcessErrors', 'GetBasePath',
        'GenerateForm', 'SearchInit' , 'PaginateInit',
        'LookUpInit', 'OrganizationList', 'inventory_script',
        '$scope', 'transitionTo',
        function(
            Rest, Wait,
            inventoryScriptsFormObject, ProcessErrors, GetBasePath,
            GenerateForm, SearchInit, PaginateInit,
            LookUpInit, OrganizationList, inventory_script,
            $scope, transitionTo
        ) {
            var generator = GenerateForm,
                id = inventory_script.id,
                form = inventoryScriptsFormObject,
                master = {},
                url = GetBasePath('inventory_scripts');

            $scope.inventory_script = inventory_script;
            generator.inject(form, {
                    mode: 'edit' ,
                    scope:$scope,
                    breadCrumbs: true,
                    related: false,
                    activityStream: false
                });
            generator.reset();
            LookUpInit({
                    url: GetBasePath('organization'),
                    scope: $scope,
                    form: form,
                    // hdr: "Select Custom Inventory",
                    list: OrganizationList,
                    field: 'organization',
                    input_type: 'radio'
                });

            // Retrieve detail record and prepopulate the form
            Wait('start');
            Rest.setUrl(url + id+'/');
            Rest.get()
                .success(function (data) {
                    var fld;
                    for (fld in form.fields) {
                        if (data[fld]) {
                            $scope[fld] = data[fld];
                            master[fld] = data[fld];
                        }

                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }
                    Wait('stop');
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to retrieve inventory script: ' + id + '. GET status: ' + status });
                });

            $scope.formSave = function () {
                generator.clearApiErrors();
                Wait('start');
                Rest.setUrl(url+ id+'/');
                Rest.put({
                    name: $scope.name,
                    description: $scope.description,
                    organization: $scope.organization,
                    script: $scope.script
                })
                    .success(function () {
                        transitionTo('inventoryScriptsList');
                        Wait('stop');

                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to add new inventory script. PUT returned status: ' + status });
                    });
            };

            $scope.formReset = function () {
                generator.reset();
                for (var fld in master) {
                    $scope[fld] = master[fld];
                }
                $scope.organization_name = master.organization_name;

            };

        }
    ];
