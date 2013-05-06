/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  RefreshRelatedHelper
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

angular.module('RefreshRelatedHelper', ['RestServices', 'Utilities'])  
    .factory('RefreshRelated', ['Alert', 'Rest', function(Alert, Rest) {
    return function(params) {
        
        var scope = params.scope; 
        var set = params.set;
        var iterator = params.iterator; 
        var url = params.url;

        url.replace(/page_size\=\d+/,'');  //stop repeatedly appending page_size

        Rest.setUrl(url);
        Rest.get({ params: { page_size: scope[iterator + 'PageSize'] }})
            .success( function(data, status, headers, config) {
                scope[set] = data['results'];
                scope[iterator + 'NextUrl'] = data.next;
                scope[iterator + 'PrevUrl'] = data.previous;
                scope[iterator + 'Count'] = data.count;
                scope[iterator + 'PageCount'] = Math.ceil((data.count / scope[iterator + 'PageSize']));
                scope[iterator + 'SearchSpin'] = false;
                })
            .error ( function(data, status, headers, config) {
                scope[iterator + 'SearchSpin'] = true;
                Alert('Error!', 'Failed to retrieve related set: ' + set + '. GET returned status: ' + status);
                });
        }
        }]);