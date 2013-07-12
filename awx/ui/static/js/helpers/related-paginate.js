/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  RelatedPaginateHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  RelatedPaginateInit({
 *      scope: <scope>,
 *      relatedSets: <array of related collections {model_name, url, iterator}>,
 *      form: <form object used by FormGenerator>
 *      });   
 *
 */

angular.module('RelatedPaginateHelper', ['RefreshRelatedHelper', 'ngCookies'])  
    .factory('RelatedPaginateInit', [ 'RefreshRelated', '$cookieStore', function(RefreshRelated, $cookieStore) {
    return function(params) {
        
        var scope = params.scope;
        var relatedSets = params.relatedSets; 

        for (var key in relatedSets){ 
            cookieSize = $cookieStore.get(relatedSets[key].iterator + 'PageSize');
            if (cookieSize) {
              // use the size found in session cookie, when available
              scope[relatedSets[key].iterator + 'PageSize'] = cookieSize;
            }
            else {
              scope[relatedSets[key].iterator + 'Page'] = 0;
              scope[relatedSets[key].iterator + 'PageSize'] = 10;
            }
        }

        scope.nextSet = function(set, iterator) {
           scope[iterator + 'Page']++;
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'NextUrl'] });
           };
                                     
        scope.prevSet = function(set, iterator) {
           scope[iterator + 'Page']--;
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: scope[iterator + 'PrevUrl'] });
           };

        scope.changePageSize = function(set, iterator) {
           // Called when a new page size is selected
           var url;
           scope[iterator + 'Page'] = 0;
           for (var key in relatedSets) {
               if (key == set) {
                  url = relatedSets[key].url;
                  break;
               }
           }
           
           // Using the session cookie, keep track of user rows per page selection
           $cookieStore.put(iterator + 'PageSize', scope[iterator + 'PageSize']);
           
           url = url.replace(/\/\?.*$/,'/');
           url += (scope[iterator + 'SearchParams']) ? scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + 'PageSize' ] :
               '?page_size=' + scope[iterator + 'PageSize' ];
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: url });  
           }
        }
        }]);