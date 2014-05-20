/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryHelper
 *  Routines for building the tree. Everything related to the tree is here except
 *  for the menu piece. The routine for building the menu is in InventoriesEdit controller
 *  (controllers/Inventories.js)
 *
 */

'use strict';

angular.module('InventoryHelper', ['RestServices', 'Utilities', 'OrganizationListDefinition', 'ListGenerator', 'AuthService',
    'InventoryHelper', 'InventoryFormDefinition', 'ParseHelper', 'SearchHelper', 'VariablesHelper',
])

.factory('GetContainerHeight', [ function() {
    return function() {
        return $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() - $('#breadcrumbs').outerHeight() -
            $('.site-footer').outerHeight() - $('#groups-container .list-actions').outerHeight() - $('#groups-table-header').height() - 15;
    };
}])

.factory('SetGroupContainerHeight', [ 'GetContainerHeight', function(GetContainerHeight) {
    return function() {
        var height;
        if ($(window).width() > 1210) {
            height = GetContainerHeight();
            $('#groups-container .list-table-container').height(height);
        }
        else {
            $('#groups-container .list-table-container').height('auto');
        }
        $('#groups-container .list-table-container').mCustomScrollbar("update");
    };
}])
.factory('WatchInventoryWindowResize', ['ApplyEllipsis', 'SetGroupContainerHeight',
    function (ApplyEllipsis, SetGroupContainerHeight) {
        return function () {
            // Call to set or restore window resize
            SetGroupContainerHeight();
            $(window).resize(_.debounce(function() {
                // Hack to stop group-name div slipping to a new line
                $('#groups_table .name-column').each(function () {
                    var td_width = $(this).width(),
                        level_width = $(this).find('.level').width(),
                        level_padding = parseInt($(this).find('.level').css('padding-left').replace(/px/, '')),
                        level = level_width + level_padding,
                        pct = (100 - Math.ceil((level / td_width) * 100)) + '%';
                    $(this).find('.group-name').css({ width: pct });
                });
                ApplyEllipsis('#groups_table .group-name a');
                ApplyEllipsis('#hosts_table .host-name a');
                SetGroupContainerHeight();
            }, 500));
        };
    }
])

.factory('SaveInventory', ['InventoryForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList',
    'GetBasePath', 'ParseTypeChange', 'Wait', 'ToJSON',
    function (InventoryForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange, Wait,
        ToJSON) {
        return function (params) {

            // Save inventory property modifications

            var scope = params.scope,
                form = InventoryForm,
                defaultUrl = GetBasePath('inventory'),
                fld, json_data, data;

            Wait('start');

            // Make sure we have valid variable data
            json_data = ToJSON(scope.inventoryParseType, scope.inventory_variables);

            data = {};
            for (fld in form.fields) {
                if (fld !== 'inventory_variables') {
                    if (form.fields[fld].realName) {
                        data[form.fields[fld].realName] = scope[fld];
                    } else {
                        data[fld] = scope[fld];
                    }
                }
            }

            Rest.setUrl(defaultUrl + scope.inventory_id + '/');
            Rest.put(data)
                .success(function (data) {
                    if (scope.inventory_variables) {
                        Rest.setUrl(data.related.variable_data);
                        Rest.put(json_data)
                            .success(function () {
                                Wait('stop');
                                scope.$emit('InventorySaved');
                            })
                            .error(function (data, status) {
                                ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                                    msg: 'Failed to update inventory varaibles. PUT returned status: ' + status
                                });
                            });
                    } else {
                        scope.$emit('InventorySaved');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to update inventory. POST returned status: ' + status });
                });
        };
    }
])


.factory('EditInventoryProperties', ['InventoryForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList',
    'GetBasePath', 'ParseTypeChange', 'SaveInventory', 'Wait', 'Store', 'SearchInit', 'ParseVariableString',
    function (InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange, SaveInventory,
        Wait, Store, SearchInit, ParseVariableString) {
        return function (params) {

            var parent_scope = params.scope,
                inventory_id = params.inventory_id,
                generator = GenerateForm,
                form = InventoryForm,
                master = {},
                PreviousSearchParams = Store('CurrentSearchParams'),
                scope;

            form.well = false;
            scope = generator.inject(form, { mode: 'edit', modal: true, related: false, modal_show: false });

            /* Reset form properties. Otherwise it screws up future requests of the Inventories detail page */
            form.well = true;

            scope.$on('inventoryPropertiesLoaded', function() {
                var callback = function() { Wait('stop'); };
                $('#form-modal').modal('show');
                scope.inventoryParseType = 'yaml';
                ParseTypeChange({ scope: scope, variable: 'inventory_variables', parse_variable: 'inventoryParseType',
                    field_id: 'inventory_inventory_variables', onReady: callback });
            });

            scope.formModalActionLabel = 'Save';
            scope.formModalCancelShow = true;
            scope.formModalInfo = false;
            scope.formModalHeader = 'Inventory Properties';

            Wait('start');
            Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
            Rest.get()
                .success(function (data) {
                    var fld;
                    for (fld in form.fields) {
                        if (fld === 'inventory_variables') {
                            scope.inventory_variables = ParseVariableString(data.variables);
                            master.inventory_variables = scope.variables;
                        } else if (fld === 'inventory_name') {
                            scope[fld] = data.name;
                            master[fld] = scope[fld];
                        } else if (fld === 'inventory_description') {
                            scope[fld] = data.description;
                            master[fld] = scope[fld];
                        } else if (data[fld]) {
                            scope[fld] = data[fld];
                            master[fld] = scope[fld];
                        }
                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }

                    LookUpInit({
                        scope: scope,
                        form: form,
                        current_item: scope.organization,
                        list: OrganizationList,
                        field: 'organization'
                    });

                    scope.$emit('inventoryPropertiesLoaded');

                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                });

            if (scope.removeInventorySaved) {
                scope.removeInventorySaved();
            }
            scope.removeInventorySaved = scope.$on('InventorySaved', function () {
                $('#form-modal').modal('hide');
                // Restore prior search state
                if (scope.searchCleanp) {
                    scope.searchCleanup();
                }
                SearchInit({
                    scope: parent_scope,
                    set: PreviousSearchParams.set,
                    list: PreviousSearchParams.list,
                    url: PreviousSearchParams.defaultUrl,
                    iterator: PreviousSearchParams.iterator,
                    sort_order: PreviousSearchParams.sort_order,
                    setWidgets: false
                });
                parent_scope.$emit('RefreshInventories');
            });

            scope.cancelModal = function () {
                // Restore prior search state
                if (scope.searchCleanp) {
                    scope.searchCleanup();
                }
                SearchInit({
                    scope: parent_scope,
                    set: PreviousSearchParams.set,
                    list: PreviousSearchParams.list,
                    url: PreviousSearchParams.defaultUrl,
                    iterator: PreviousSearchParams.iterator,
                    sort_order: PreviousSearchParams.sort_order,
                    setWidgets: false
                });
            };

            scope.formModalAction = function () {
                scope.inventory_id = inventory_id;
                parent_scope.inventory_name = scope.inventory_name;
                SaveInventory({ scope: scope });
            };

        };
    }
]);