/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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
 
angular.module('RefreshHelper', ['RestServices', 'Utilities', 'PaginationHelpers'])  
    .factory('Refresh', ['ProcessErrors', 'Rest', 'Wait', 'Empty', 'PageRangeSetup', 
    function(ProcessErrors, Rest, Wait, Empty, PageRangeSetup) {
    return function(params) {
        
        var scope = params.scope; 
        var set = params.set;
        var iterator = params.iterator; 
        var url = params.url;

        scope.current_url = url;
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                PageRangeSetup({ scope: scope, count: data.count, next: data.next, previous: data.previous, iterator: iterator });
                scope[iterator + 'Loading'] = false;
                for (var i=1; i <= 3; i++) {
                    var modifier = (i == 1) ? '' : i;
                    scope[iterator + 'HoldInput' + modifier] = false;
                }
                scope[set] = data['results'];
                window.scrollTo(0,0);
                Wait('stop');
                scope.$emit('PostRefresh');
                })
            .error ( function(data, status, headers, config) {
                scope[iterator + 'HoldInput'] = false;
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status });
                });
        }
        }]);