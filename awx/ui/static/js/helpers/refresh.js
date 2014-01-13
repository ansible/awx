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
 
angular.module('RefreshHelper', ['RestServices', 'Utilities'])  
    .factory('Refresh', ['ProcessErrors', 'Rest', 'Wait', function(ProcessErrors, Rest, Wait) {
    return function(params) {
        
        var scope = params.scope; 
        var set = params.set;
        var iterator = params.iterator; 
        var url = params.url;
        console.log('Inside refresh');
        console.log(url);
        scope.current_url = url;
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                Wait('stop');
                scope[iterator + 'NextUrl'] = data.next;
                scope[iterator + 'PrevUrl'] = data.previous;
                scope[iterator + 'Count'] = data.count;
                scope[iterator + 'PageCount'] = Math.ceil((data.count / scope[iterator + 'PageSize']));
                //scope[iterator + 'SearchSpin'] = false;
                scope[iterator + 'Loading'] = false;
                for (var i=1; i <= 3; i++) {
                    var modifier = (i == 1) ? '' : i;
                    scope[iterator + 'HoldInput' + modifier] = false;
                }
                scope[set] = data['results'];
                scope.$emit('PostRefresh');
                })
            .error ( function(data, status, headers, config) {
                Wait('stop');
                //scope[iterator + 'SearchSpin'] = false;
                scope[iterator + 'HoldInput'] = false;
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status });
                });
        }
        }]);