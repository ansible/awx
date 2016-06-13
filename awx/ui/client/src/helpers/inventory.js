/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:Inventory
 * @description   InventoryHelper
 *  Routines for building the tree. Everything related to the tree is here except
 *  for the menu piece. The routine for building the menu is in InventoriesEdit controller
 *  (controllers/Inventories.js)
*/

import listGenerator from '../shared/list-generator/main';

export default
    angular.module('InventoryHelper', ['RestServices', 'Utilities', 'OrganizationListDefinition', listGenerator.name,
        'InventoryHelper', 'InventoryFormDefinition', 'ParseHelper', 'SearchHelper', 'VariablesHelper',
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
                        if (scope.variables) {
                            scope.$emit('UpdateInventoryVariables', data);
                        } else {
                            scope.$emit('InventorySaved');
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to update inventory. PUT returned status: ' + status });
                    });
            };
        }
    ]);
