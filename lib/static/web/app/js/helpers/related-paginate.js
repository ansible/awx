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

angular.module('RelatedPaginateHelper', ['RefreshRelatedHelper'])  
    .factory('RelatedPaginateInit', [ 'RefreshRelated', function(RefreshRelated) {
    return function(params) {
        
        var scope = params.scope;
        var relatedSets = params.relatedSets; 

        for (var key in relatedSets){
            scope[relatedSets[key].iterator + 'Page'] = 0;
            scope[relatedSets[key].iterator + 'PageSize'] = 20;
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
           var defaultUrl;
           scope[iterator + 'Page'] = 0;
           for (var key in relatedSets) {
               if (key == set) {
                  defaultUrl = relatedSets[key].url;
                  break;
               }
           }
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: defaultUrl });  
           }
        }
        }]);