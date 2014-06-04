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


.factory('GetGroupContainerHeight', [ function() {
    return function() {

      /*console.log('window height: ' + $(window).height());
        console.log('main-menu: ' + $('.main-menu').outerHeight());
        console.log('main_tabs: ' + $('#main_tabs').outerHeight());
        console.log('breadcrumbs: ' + $('#breadcrumbs').outerHeight());
        console.log('footer: ' + $('.site-footer').outerHeight());
        console.log('group-breadcrumbs: ' + $('.group-breadcrumbs').outerHeight());
        console.log('searchwidget: ' + $('#groups-container #search-widget-container').outerHeight());
        console.log('group table head: ' + $('#groups_table thead').height());
        console.log('subtotal: ' + ( $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() - $('#breadcrumbs').outerHeight() -
            $('.site-footer').outerHeight() - $('.group-breadcrumbs').outerHeight() - $('#groups-container #search-widget-container').outerHeight() -
            $('#groups_table thead').height() ));
      */
        return $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() - $('#breadcrumbs').outerHeight() -
            $('.site-footer').outerHeight() - $('.group-breadcrumbs').outerHeight() - $('#groups-container #search-widget-container').outerHeight() -
            $('#groups_table thead').height() - 70;
    };
}])

.factory('GetHostContainerRows', [ function() {
    return function() {
        var height = $('#hosts-container .well').height() - $('#hosts-constainer .well .row').height() - $('#hosts_table thead').height();
        return Math.floor(height / 30) - 2;
    };
}])

.factory('GetGroupContainerRows', [ function() {
    return function() {
        var height = $('#groups-container .list-table-container').height();
        return Math.floor(height / 31) - 2;
    };
}])

.factory('SetContainerHeights', [ 'GetGroupContainerHeight', 'GetHostContainerRows', function(GetGroupContainerHeight, GetHostContainerRows) {
    return function(params) {
        var group_scope = params.group_scope,
            host_scope = params.host_scope,
            reloadHosts = (params && params.reloadHosts) ? true : false,
            height, rows;
        if ($(window).width() > 1210) {
            height = GetGroupContainerHeight();
            $('#groups-container .list-table-container').height(height);
            $('#hosts-container .well').height( $('#groups-container .well').height());
        }
        else {
            $('#groups-container .list-table-container').height('auto');
            $('#hosts-container .well').height('auto');
        }
        //$('#groups-container .list-table-container').mCustomScrollbar("update");

        if (reloadHosts) {
            // we need ro recalc the the page size
            if ($(window).width() > 1210) {
                rows = GetHostContainerRows();
                host_scope.host_page_size = rows;
                group_scope.group_page_size = rows;
            }
            else {
                // on small screens we go back to the default
                host_scope.host_page_size = 20;
                group_scope.group_page_size = 20;
            }
            host_scope.changePageSize('hosts', 'host');
            group_scope.changePageSize('groups', 'group');
        }
    };
}])


.factory('WatchInventoryWindowResize', ['ApplyEllipsis', 'SetContainerHeights',
    function (ApplyEllipsis, SetContainerHeights) {
        return function (params) {
            // Call to set or restore window resize
            var group_scope = params.group_scope,
                host_scope = params.host_scope;
            $(window).off("resize");
            $(window).resize(_.debounce(function() {
                // Hack to stop group-name div slipping to a new line
                //$('#groups_table .name-column').each(function () {
                //    var td_width = $(this).width(),
                //        level_width = $(this).find('.level').width(),
                //        level_padding = parseInt($(this).find('.level').css('padding-left').replace(/px/, '')),
                //        level = level_width + level_padding,
                //        pct = (100 - Math.ceil((level / td_width) * 100)) + '%';
                //    $(this).find('.group-name').css({ width: pct });
                //});
                ApplyEllipsis('#groups_table .group-name a');
                ApplyEllipsis('#hosts_table .host-name a');
                SetContainerHeights({
                    group_scope: group_scope,
                    host_scope: host_scope,
                    reloadHosts: true
                });
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
            json_data = ToJSON(scope.parseType, scope.variables);

            data = {};
            for (fld in form.fields) {
                if (fld !== 'variables') {
                    if (form.fields[fld].realName) {
                        data[form.fields[fld].realName] = scope[fld];
                    } else {
                        data[fld] = scope[fld];
                    }
                }
            }

            if (scope.removeUpdateInventoryVariables) {
                scope.removeUpdateInventoryVariables();
            }
            scope.removeUpdateInventoryVariables = scope.$on('UpdateInventoryVariables', function(e, data) {
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
            });

            Rest.setUrl(defaultUrl + scope.inventory_id + '/');
            Rest.put(data)
                .success(function (data) {
                    if (scope.inventory_variables) {
                        scope.$emit('UpdateInventoryVariables', data);
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
    'GetBasePath', 'ParseTypeChange', 'SaveInventory', 'Wait', 'Store', 'SearchInit', 'ParseVariableString', 'CreateDialog', 'TextareaResize',
    function (InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange, SaveInventory,
        Wait, Store, SearchInit, ParseVariableString, CreateDialog, TextareaResize) {
        return function (params) {

            var parent_scope = params.scope,
                inventory_id = params.inventory_id,
                generator = GenerateForm,
                form = InventoryForm,
                master = {},
                //PreviousSearchParams = Store('CurrentSearchParams'),
                buttons,
                scope = parent_scope.$new();

            form.well = false;

            generator.inject(form, {
                mode: 'edit',
                showButtons: false,
                showActions: false,
                id: 'inventory-edit-modal-dialog',
                breadCrumbs: false,
                related: false,
                scope: scope
            });

            /* Reset form properties. Otherwise it screws up future requests of the Inventories detail page */
            form.well = true;

            buttons = [{
                label: "Cancel",
                onClick: function() {
                    scope.cancelModal();
                },
                icon: "fa-times",
                "class": "btn btn-default",
                "id": "inventory-edit-cancel-button"
            },{
                label: "Save",
                onClick: function() {
                    scope.saveModal();
                },
                icon: "fa-check",
                "class": "btn btn-primary",
                "id": "inventory-edit-save-button"
            }];

            CreateDialog({
                scope: scope,
                buttons: buttons,
                width: 675,
                height: 750,
                minWidth: 400,
                title: 'Inventory Properties',
                id: 'inventory-edit-modal-dialog',
                clonseOnEscape: false,
                onClose: function() {
                    Wait('stop');
                    scope.codeMirror.destroy();
                    $('#inventory-edit-modal-dialog').empty();
                },
                onResizeStop: function() {
                    TextareaResize({
                        scope: scope,
                        textareaId: 'inventory_variables',
                        modalId: 'inventory-edit-modal-dialog',
                        formId: 'inventory_form'
                    });
                },
                beforeDestroy: function() {
                    if (scope.codeMirror) {
                        scope.codeMirror.destroy();
                    }
                    $('#inventory-edit-modal-dialog').empty();
                },
                onOpen: function() {
                    $('#inventory_name').focus();
                    setTimeout(function() {
                        TextareaResize({
                            scope: scope,
                            textareaId: 'inventory_variables',
                            modalId: 'inventory-edit-modal-dialog',
                            formId: 'inventory_form',
                            parse: true
                        });
                    }, 300);
                },
                callback: 'InventoryEditDialogReady'
            });

            scope.parseType = 'yaml';

            if (scope.removeInventoryPropertiesLoaded) {
                scope.removeInventoryPropertiesLoaded();
            }
            scope.removeInventoryPropertiesLoaded = scope.$on('inventoryPropertiesLoaded', function() {
                Wait('stop');
                $('#inventory-edit-modal-dialog').dialog('open');
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
                        if (fld === 'variables') {
                            scope.variables = ParseVariableString(data.variables);
                            master.variables = scope.variables;
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
                //$('#form-modal').modal('hide');
                // Restore prior search state
                //if (scope.searchCleanp) {
                //    scope.searchCleanup();
                //}
                //SearchInit({
                //    scope: parent_scope,
                //    set: PreviousSearchParams.set,
                //    list: PreviousSearchParams.list,
                //    url: PreviousSearchParams.defaultUrl,
                //    iterator: PreviousSearchParams.iterator,
                //    sort_order: PreviousSearchParams.sort_order,
                //    setWidgets: false
                //});
                //parent_scope.$emit('RefreshInventories');
                try {
                    $('#inventory-edit-modal-dialog').dialog('close');
                }
                catch(err) {
                    // ignore
                }
                scope.$destroy();
            });

            scope.cancelModal = function () {
                // Restore prior search state
                /*if (scope.searchCleanp) {
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
                });*/
                try {
                    $('#inventory-edit-modal-dialog').dialog('close');
                }
                catch(err) {
                    // ignore
                }
                scope.$destroy();
            };

            scope.saveModal = function () {
                scope.inventory_id = inventory_id;
                parent_scope.inventory_name = scope.inventory_name;
                SaveInventory({ scope: scope });
            };

        };
    }
]);