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

'use strict';

angular.module('RefreshHelper', ['RestServices', 'Utilities', 'PaginationHelpers'])
    .factory('Refresh', ['ProcessErrors', 'Rest', 'Wait', 'Empty', 'PageRangeSetup',
        function (ProcessErrors, Rest, Wait, Empty, PageRangeSetup) {
            return function (params) {

                var scope = params.scope,
                    set = params.set,
                    iterator = params.iterator,
                    url = params.url;
                
                scope[iterator + 'Loading'] = true;
                scope.current_url = url;
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        var i, modifier;
                        PageRangeSetup({
                            scope: scope,
                            count: data.count,
                            next: data.next,
                            previous: data.previous,
                            iterator: iterator
                        });
                        for (i = 1; i <= 3; i++) {
                            modifier = (i === 1) ? '' : i;
                            scope[iterator + 'HoldInput' + modifier] = false;
                        }
                        scope[set] = data.results;
                        scope[iterator + 'Loading'] = false;
                        Wait('stop');
                        scope.$emit('PostRefresh');
                    })
                    .error(function (data, status) {
                        scope[iterator + 'HoldInput'] = false;
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status
                        });
                    });
            };
        }
    ]);