/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  RefreshHelper
 *
 *  Used to refresh a related set whenever pagination or filter options change.
 *
 *  RefreshRelated({
 *      scope: <current scope>,
 *      set: <model>,
 *      iterator: <model name in singular form (i.e. organization),
 *      url: <the api url to call>       
 *      });   
 *
 */
 
angular.module('RefreshHelper', ['RestServices', 'Utilities'])  
    .factory('Refresh', ['Alert', 'Rest', function(Alert, Rest) {
    return function(params) {
        
        var scope = params.scope; 
        var set = params.set;
        var iterator = params.iterator; 
        var url = params.url;
       
        url.replace(/page_size\=\d+/,'');  //stop repeatedly appending page_size
        url += scope[iterator + 'SearchParams'];
        Rest.setUrl(url);
        Rest.get({ params: { page_size: scope[iterator + 'PageSize'] }})
            .success( function(data, status, headers, config) {
                scope[iterator + 'NextUrl'] = data.next;
                scope[iterator + 'PrevUrl'] = data.previous;
                scope[iterator + 'Count'] = data.count;
                scope[iterator + 'PageCount'] = Math.ceil((data.count / scope[iterator + 'PageSize']));
                if (set == 'inventories') {
                   lookup_results = [];
                   scope.$emit('refreshFinished', data['results']);
                }
                else {
                   scope[iterator + 'SearchSpin'] = false;
                   scope[set] = data['results'];
                }
                })
            .error ( function(data, status, headers, config) {
                scope[iterator + 'SearchSpin'] = true;
                Alert('Error!', 'Failed to retrieve ' + set + '. GET returned status: ' + status);
                });
        }
        }]);