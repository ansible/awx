/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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

'use strict';

angular.module('RefreshRelatedHelper', ['RestServices', 'Utilities', 'PaginationHelpers'])
    .factory('RefreshRelated', ['ProcessErrors', 'Rest', 'Wait', 'PageRangeSetup',
        function (ProcessErrors, Rest, Wait, PageRangeSetup) {
            return function (params) {

                var scope = params.scope,
                    set = params.set,
                    iterator = params.iterator,
                    url = params.url;

                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        PageRangeSetup({
                            scope: scope,
                            count: data.count,
                            next: data.next,
                            previous: data.previous,
                            iterator: iterator
                        });
                        scope[set] = data.results;
                        scope[iterator + 'Loading'] = false;
                        scope[iterator + 'HoldInput'] = false;
                        Wait('stop');
                        scope.$emit('related' + set);
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status });
                    });
            };
        }
    ]);