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
 *      field: <name of the form field with which the lookup is associated>,
 *      hdr: <optional. modal dialog header>
 *      })
 */
 
angular.module('LookUpHelper', [ 'RestServices', 'Utilities', 'SearchHelper', 'PaginateHelper', 'ListGenerator', 'ApiLoader' ])  
    .factory('LookUpInit', ['Alert', 'Rest', 'GenerateList', 'SearchInit', 'PaginateInit', 'GetBasePath', 'FormatDate',
    function(Alert, Rest, GenerateList, SearchInit, PaginateInit, GetBasePath, FormatDate) {
    return function(params) {
        
        var scope = params.scope;  // form scope
        var form = params.form;    // form object
        var current_item = params.current_item;    //id of the item that should be selected on open
        var list = params.list;    // list object
        var field = params.field;  // form field
        var postAction = params.postAction  //action to perform post user selection
        
        // Show pop-up 
        var name = list.iterator.charAt(0).toUpperCase() + list.iterator.substring(1);
        var defaultUrl = (list.name == 'inventories') ? GetBasePath('inventory') : GetBasePath(list.name);
        var hdr = (params.hdr) ? params.hdr : 'Select ' + name;

        $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-url',defaultUrl + 
            '?' + form.fields[field].sourceField + '__' + 'iexact=:value');
        $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-source',field);

        scope['lookUp' + name] = function() {
            var listGenerator = GenerateList;
            var listScope = listGenerator.inject(list, { mode: 'lookup', hdr: hdr });
            listScope = scope;
            listScope.selectAction = function() {
                var found = false;
                var name;
                for (var i=0; i < listScope[list.name].length; i++) {
                    if (listScope[list.name][i]['checked'] == '1') {
                       found = true;
                       scope[field] = listScope[list.name][i].id;
                       if (scope[form.name + '_form'] && form.fields[field] && form.fields[field].sourceModel) {
                          scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] = 
                              listScope[list.name][i][form.fields[field].sourceField];
                          if (scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                             scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]
                                 .$setValidity('awlookup',true);
                          }
                       }
                       if (scope[form.name + '_form']) {
                          scope[form.name + '_form'].$setDirty();
                       }
                       listGenerator.hide();
                    }
                } 
                if (found == false) {
                   Alert('Missing Selection', 'Oops, you failed to make a selection. Click on a row to make your selection, ' +
                       'and then click the Select button.');
                }
                else {
                   if (postAction) {
                       postAction();
                   }
                }
                }

            listScope['toggle_' + list.iterator] = function(id) {
                for (var i=0; i < scope[list.name].length; i++) {
                    if (listScope[list.name][i]['id'] == id) {
                       listScope[list.name][i]['checked'] = '1';
                       listScope[list.name][i]['success_class'] = 'success';
                    }
                    else {
                       listScope[list.name][i]['checked'] = '0';
                       listScope[list.name][i]['success_class'] = '';
                    }
                }
                }
                
            SearchInit({ scope: listScope, set: list.name, list: list, url: defaultUrl });
            PaginateInit({ scope: listScope, list: list, url: defaultUrl, mode: 'lookup' });
            
            // If user made a selection previously, mark it as selected when modal loads 
            if (listScope.lookupPostRefreshRemove) {
                listScope.lookupPostRefreshRemove();
            }
            listScope.lookupPostRefreshRemove = scope.$on('PostRefresh', function() {
                for (var fld in list.fields) {
                   if (list.fields[fld].type && list.fields[fld].type == 'date') {
                      //convert dates to our standard format
                      for (var i=0; i < scope[list.name].length; i++) {
                          scope[list.name][i][fld] = FormatDate(new Date(scope[list.name][i][fld]));
                      }
                   } 
                }
                listScope['toggle_' + list.iterator](scope[field]);
                });

            listScope.search(list.iterator);
            
            }
        }
        }]);


