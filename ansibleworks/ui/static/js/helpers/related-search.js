/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  RelatedSearchHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  SearchInit({
 *      scope: <scope>,
 *      relatedSets: <array of related collections {model_name, url, iterator}>,
 *      form: <form object used by FormGenerator>
 *      });   
 *
 *
 */

angular.module('RelatedSearchHelper', ['RestServices', 'Utilities','RefreshRelatedHelper'])  
    .factory('RelatedSearchInit', ['Alert', 'Rest', 'RefreshRelated', function(Alert, Rest, RefreshRelated) {
    return function(params) {
        
        var scope = params.scope;
        var relatedSets = params.relatedSets;
        var form = params.form; 

        // Set default values
        for (var set in form.related) {
            if (form.related[set].type != 'tree') {
                for (var fld in form.related[set].fields) {
                    if (form.related[set].fields[fld].key) {
                       scope[form.related[set].iterator + 'SearchField'] = fld
                       scope[form.related[set].iterator + 'SearchFieldLabel'] = form.related[set].fields[fld].label;
                       break;
                    }
                }
                scope[form.related[set].iterator + 'SearchType'] = 'contains';
                scope[form.related[set].iterator + 'SearchTypeLabel'] = 'Contains';
                scope[form.related[set].iterator + 'SelectShow'] = false;
                scope[form.related[set].iterator + 'HideSearchType'] = false;
            }
        } 
        
        // Functions to handle search widget changes
        scope.setSearchField = function(model, fld, label) {
           scope[model + 'SearchFieldLabel'] = label;
           scope[model + 'SearchField'] = fld;
           scope.search(model);
           }

        scope.setSearchType = function(model, type, label) {
           scope[model + 'SearchTypeLabel'] = label; 
           scope[model + 'SearchType'] = type;
           scope.search(model);
           }

        scope.search = function(model) {
           scope[model + 'SearchSpin'] = true;
           scope[model + 'Loading'] = true;
           
           var set, url, iterator, default_order;
           for (var key in relatedSets) {
               if (relatedSets[key].iterator == model) {
                  set = key;
                  iterator = relatedSets[key].iterator;
                  url = relatedSets[key].url;
                 
                  for (var fld in form.related[key].fields) {
                      if (form.related[key].fields[fld].key) {
                         default_order = fld;
                      }
                  }
                  break;
               }
           }
           if (scope[model + 'SearchValue'] != '' && scope[model + 'SearchValue'] != undefined) {
              scope[model + 'SearchParams'] = '?' + scope[model + 'SearchField'] + 
                     '__' + scope[model + 'SearchType'] + '=' + escape(scope[model + 'SearchValue']);
              scope[model + 'SearchParams'] += (default_order) ? '&order_by=' + escape(default_order) : '';
           }
           else {
              scope[model + 'SearchParams'] = (default_order) ? '?order_by=' + escape(default_order) : '';
           }
           url += scope[model + 'SearchParams'];
           url += (scope[model + 'PageSize']) ? '&page_size=' + scope[iterator + 'PageSize'] : "";
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: url });
           }
        }
        }]);
