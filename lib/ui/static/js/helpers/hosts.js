/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Helper
 *  Routines shared amongst the hosts controllers 
 */
 
angular.module('HostHelper', [ 'RestServices', 'Utilities', 'OrganizationListDefinition',
                               'SearchHelper', 'PaginateHelper', 'ListGenerator' ])

    .factory('LookUpInventoryInit', ['Alert', 'Rest', 'InventoryList', 'GenerateList', 'SearchInit', 'PaginateInit', 
    function(Alert, Rest, InventoryList, GenerateList, SearchInit, PaginateInit) {
    return function(params) {
        
        var scope = params.scope;

        // Show pop-up to select organization
        scope.lookUpInventory = function() {
            var list = InventoryList; 
            var listGenerator = GenerateList;
            var listScope = listGenerator.inject(list, { mode: 'lookup', hdr: 'Select Inventory' });
            var defaultUrl = '/api/v1/inventories';

            listScope.selectAction = function() {
                var found = false;
                for (var i=0; i < listScope[list.name].length; i++) {
                    if (listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] == "success") {
                       found = true; 
                       scope['inventory'] = listScope[list.name][i].id;
                       scope['inventory_name'] = listScope[list.name][i].name;
                       scope['host_form'].$setDirty();
                       listGenerator.hide();
                    }
                } 
                if (found == false) {
                   Alert('No Selection', 'Click on a row to select an Inventory before clicking the Select button.');
                }
                }

            listScope.toggle_inventory = function(id) {
                // when user clicks a row, remove 'success' class from all rows except clicked-on row
                if (listScope[list.name]) {
                   for (var i=0; i < listScope[list.name].length; i++) {
                       listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] = ""; 
                   }
                }
                if (id != null && id != undefined) {
                   listScope[list.iterator + "_" + id + "_class"] = "success";
                }
                }

            SearchInit({ scope: listScope, set: list.name, list: list, url: defaultUrl });
            PaginateInit({ scope: listScope, list: list, url: defaultUrl, mode: 'lookup' });
            scope.search(list.iterator);
            listScope.toggle_inventory(scope.inventory);
            }
        }
        }]);