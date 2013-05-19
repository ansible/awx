/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  PaginateHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  PaginateInit({
 *      scope: <scope>,
 *      list:  <form object used by FormGenerator>
 *      url:   <
 *      });   
 *
 */

angular.module('PaginateHelper', ['RefreshHelper'])  
    .factory('PaginateInit', [ 'Refresh', function(Refresh) {
    return function(params) {
        
        var scope = params.scope;
        var list = params.list;
        var url = params.url;
        var mode = (params.mode) ? params.mode : null;

        scope[list.iterator + 'Page'] = 0;

        if (mode == 'lookup') {
           scope[list.iterator + 'PageSize'] = 5;
        }
        else {
           scope[list.iterator + 'PageSize'] = 20;
        }

        scope.nextSet = function(set, iterator) {
           scope[iterator + 'Page']++;
           Refresh({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'NextUrl'] });
           };
                                     
        scope.prevSet = function(set, iterator) {
           scope[iterator + 'Page']--;
           Refresh({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'PrevUrl'] });
           };

        scope.changePageSize = function(set, iterator) {
           // Called when a new page size is selected
           scope[iterator + 'Page'] = 0;
           url += (scope[iterator + 'SearchParams']) ? scope[iterator + 'SearchParams'] : '';
           Refresh({ scope: scope, set: set, iterator: iterator, url: url });  
           }
        }
        }]);