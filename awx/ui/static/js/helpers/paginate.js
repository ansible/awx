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

angular.module('PaginateHelper', ['RefreshHelper', 'ngCookies'])  
    .factory('PaginateInit', [ 'Refresh', '$cookieStore', function(Refresh, $cookieStore) {
    return function(params) {
        
        var scope = params.scope;
        var list = params.list;
        var iterator = (params.iterator) ? params.iterator : list.iterator;
        var url = params.url;
        var mode = (params.mode) ? params.mode : null;
        var cookieSize = $cookieStore.get(iterator + 'PageSize');
        
        if (params.page) {
           scope[iterator + 'Page'] = params.page;
        }
        else {
          scope[iterator + 'Page'] = 0;
        }

        if (cookieSize && mode != 'lookup') {
           // use the size found in session cookie, when available
           scope[iterator + 'PageSize'] = cookieSize;
        }
        else {
           if (params.pageSize) {
              scope[iterator + 'PageSize'] = params.pageSize;
           }
           else if (mode == 'lookup') {
                 scope[iterator + 'PageSize'] = 5;
           }
           else {
                 scope[iterator + 'PageSize'] = 20;
           }
        }

        scope.nextSet = function(set, iterator) {
           if (scope[iterator + 'NextUrl']) {
              scope[iterator + 'Page']++;
              Refresh({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'NextUrl'] });
           }
           };
                                     
        scope.prevSet = function(set, iterator) {
           if (scope[iterator + 'PrevUrl']) {
              scope[iterator + 'Page']--;
              Refresh({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'PrevUrl'] });
           }
           };

        scope.changePageSize = function(set, iterator) {
           // Called whenever a new page size is selected

           // Using the session cookie, keep track of user rows per page selection
           $cookieStore.put(iterator + 'PageSize', scope[iterator + 'PageSize']);
           
           scope[iterator + 'Page'] = 0;
           var new_url = url.replace(/\?page_size\=\d+/,'');
           var connect = (/\/$/.test(new_url)) ? '?' : '&'; 
           new_url += (scope[iterator + 'SearchParams']) ? connect + scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + 'PageSize' ] :
                + connect + 'page_size=' + scope[iterator + 'PageSize' ];
           Refresh({ scope: scope, set: set, iterator: iterator, url: new_url });  
           }
        }
        }]);