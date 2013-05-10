/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  LookupHelper
 *  Build a lookup dialog
 * 
 *  LookUpInit( {
 *      scope: <form scope>,
 *      form: <form object>,
 *      current_item: <id of item to select on open>,
 *      list: <list object>,
 *      field: <name of the form field with which the lookup is associated>
 *      })
 */
 
angular.module('LookUpHelper', [ 'RestServices', 'Utilities', 'SearchHelper', 'PaginateHelper', 'ListGenerator', 'ApiLoader' ])  

    .factory('LookUpInit', ['Alert', 'Rest', 'GenerateList', 'SearchInit', 'PaginateInit', 'GetBasePath',
    function(Alert, Rest, GenerateList, SearchInit, PaginateInit, GetBasePath) {
    return function(params) {
        
        var scope = params.scope;  // form scope
        var form = params.form;    // form object
        var current_item = params.current_item;    //id of the item that should be selected on open
        var list = params.list;    // list object
        var field = params.field;  // form field

        // Show pop-up to select user
        var name = list.iterator.charAt(0).toUpperCase() + list.iterator.substring(1);
        scope['lookUp' + name] = function() {
            var listGenerator = GenerateList;
            var listScope = listGenerator.inject(list, { mode: 'lookup', hdr: 'Select ' + name });
            var defaultUrl = GetBasePath(list.name);

            listScope.selectAction = function() {
                var found = false;
                var name;
                for (var i=0; i < listScope[list.name].length; i++) {
                    if (listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] == "success") {
                       found = true; 
                       scope[field] = listScope[list.name][i].id;
                       scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] = 
                           listScope[list.name][i][form.fields[field].sourceField];
                       scope[form.name + '_form'].$setDirty();
                       listGenerator.hide();
                    }
                } 
                if (found == false) {
                   Alert('Missing Selection', 'Oops, you failed to make a selection. Click on a row to make your selection, ' +
                       'and then click the Select button.');
                }
                }

            listScope['toggle_' + list.iterator] = function(id) {
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
            listScope['toggle_' + list.iterator](current_item);
            }
        }
        }]);


