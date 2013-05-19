/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  SearchHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  SearchInit({
 *      scope:       <scope>,
 *      set:         <model name (i.e. organizations),
 *                   name was given in ng-repeat>
 *      url:         <default api url used to load data>
 *      list:        <list object used by ListGenerator>
 *      });   
 *
 */

angular.module('SearchHelper', ['RestServices', 'Utilities', 'RefreshHelper'])  
    .factory('SearchInit', ['Alert', 'Rest', 'Refresh', function(Alert, Rest, Refresh) {
    return function(params) {
        
        var scope = params.scope;
        var set = params.set; 
        var defaultUrl = params.url;
        var list = params.list; 
        var iterator = list.iterator;
        var default_order;

        // Set default values
        for (fld in list.fields) {
            if (list.fields[fld].key) {
               default_order = (list.fields[fld].desc) ? '-' + fld : fld;
               scope[iterator + 'SearchField'] = fld
               scope[iterator + 'SearchFieldLabel'] = list.fields[fld].label;
               break;
            }
        }
        scope[iterator + 'SearchType'] = 'icontains';
        scope[iterator + 'SearchTypeLabel'] = 'Contains';
        scope[iterator + 'SearchParams'] = '';
        scope[iterator + 'SearchValue'] = '';
      
        // Functions to handle search widget changes
        scope.setSearchField = function(iterator, fld, label) {
           scope[iterator + 'SearchFieldLabel'] = label;
           scope[iterator + 'SearchField'] = fld;
           scope.search(iterator);
           }

        scope.setSearchType = function(iterator, type, label) {
           scope[iterator + 'SearchTypeLabel'] = label; 
           scope[iterator + 'SearchType'] = type;
           scope.search(iterator);
           }

        scope.search = function(iterator) {
           //
           // need to be able to search by related set. Ex: /api/v1/inventories/?organization__name__icontains=
           //
           scope[iterator + 'SearchSpin'] = true;
           var url = defaultUrl;
           if (scope[iterator + 'SearchValue'] != '' && scope[iterator + 'SearchValue'] != undefined) {
              if (list.fields[scope[iterator + 'SearchField']].sourceModel) {
                 // handle fields whose source is a related model e.g. inventories.organization
                 scope[iterator + 'SearchParams'] = '?' + list.fields[scope[iterator + 'SearchField']].sourceModel + '__' + 
                 list.fields[scope[iterator + 'SearchField']].sourceField + '__' + 
                 scope[iterator + 'SearchType'] + '=' + escape(scope[iterator + 'SearchValue']); 
                 scope[iterator + 'SearchParams'] += (default_order) ? '&order_by=' + escape(default_order) : '';
              }
              else {
                 scope[iterator + 'SearchParams'] = '?' + scope[iterator + 'SearchField'] + '__' + 
                 scope[iterator + 'SearchType'] + '=' + escape(scope[iterator + 'SearchValue']);
                 scope[iterator + 'SearchParams'] += (default_order) ? '&order_by=' + escape(default_order) : '';
              }
           }
           else {
              scope[iterator + 'SearchParams'] = ''; 
              scope[iterator + 'SearchParams'] += (default_order) ? '?order_by=' + escape(default_order) : '';
           }
           url += scope[iterator + 'SearchParams'];
           url += (scope[iterator + 'PageSize']) ? '&page_size=' + scope[iterator + 'PageSize'] : "";
           Refresh({ scope: scope, set: set, iterator: iterator, url: url });
           }
        }
        }]);
