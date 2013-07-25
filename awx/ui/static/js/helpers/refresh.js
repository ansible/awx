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
        
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                scope[iterator + 'NextUrl'] = data.next;
                scope[iterator + 'PrevUrl'] = data.previous;
                scope[iterator + 'Count'] = data.count;
                scope[iterator + 'PageCount'] = Math.ceil((data.count / scope[iterator + 'PageSize']));
                scope[iterator + 'SearchSpin'] = false;
                scope[iterator + 'Loading'] = false;
                scope[set] = data['results'];
                scope.$emit('PostRefresh');
                })
            .error ( function(data, status, headers, config) {
                scope[iterator + 'SearchSpin'] = false;
                Alert('Error!', 'Failed to retrieve ' + set + '. GET returned status: ' + status);
                });
        }
        }]);