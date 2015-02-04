/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  PaginationHelpers.js
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:PaginationHelpers
 * @description  pagination
*/

export default
    angular.module('PaginationHelpers', ['Utilities', 'RefreshHelper', 'RefreshRelatedHelper'])

    .factory('PageRangeSetup', ['Empty',
        function (Empty) {
            return function (params) {

                var scope = params.scope,
                    count = params.count,
                    next = params.next,
                    previous = params.previous,
                    iterator = params.iterator,
                    i, first, last;

                scope[iterator + '_page'] = 1;
                scope[iterator + '_num_pages'] = Math.ceil((count / scope[iterator + '_page_size']));
                scope[iterator + '_num_pages'] = (scope[iterator + '_num_pages'] <= 0) ? 1 : scope[iterator + '_num_pages'];
                scope[iterator + '_total_rows'] = count;

                // Which page are we on?
                if (Empty(next) && previous) {
                    // no next page, but there is a previous page
                    scope[iterator + '_page'] = parseInt(previous.match(/page=\d+/)[0].replace(/page=/, '')) + 1;
                } else if (next && Empty(previous)) {
                    // next page available, but no previous page
                    scope[iterator + '_page'] = 1;
                } else if (next && previous) {
                    // we're in between next and previous
                    scope[iterator + '_page'] = parseInt(previous.match(/page=\d+/)[0].replace(/page=/, '')) + 1;
                }

                // Calc the range of up to 10 pages to show
                scope[iterator + '_page_range'] = [];
                first = (scope[iterator + '_page'] > 5) ? scope[iterator + '_page'] - 5 : 1;
                if (scope[iterator + '_page'] < 6) {
                    last = (10 <= scope[iterator + '_num_pages']) ? 10 : scope[iterator + '_num_pages'];
                } else {
                    last = (scope[iterator + '_page'] + 4 < scope[iterator + '_num_pages']) ?
                        scope[iterator + '_page'] + 4 : scope[iterator + '_num_pages'];
                }
                for (i = first; i <= last; i++) {
                    scope[iterator + '_page_range'].push(i);
                }
            };
        }
    ])

    .factory('RelatedPaginateInit', ['RefreshRelated', '$cookieStore', 'Wait',
        function (RefreshRelated, $cookieStore, Wait) {
            return function (params) {

                var scope = params.scope,
                    relatedSets = params.relatedSets,
                    pageSize = (params.pageSize) ? params.pageSize : 10,
                    key;

                for (key in relatedSets) {
                    scope[relatedSets[key].iterator + '_url'] = relatedSets[key].url;
                    scope[relatedSets[key].iterator + '_page'] = 0;
                    scope[relatedSets[key].iterator + '_page_size'] = pageSize;
                }

                scope.getPage = function (page, set, iterator) {
                    var new_url = scope[iterator + '_url'].replace(/.page\=\d+/, ''),
                        connect = (/\/$/.test(new_url)) ? '?' : '&';
                    new_url += connect + 'page=' + page;
                    new_url += (scope[iterator + 'SearchParams']) ? '&' + scope[iterator + 'SearchParams'] +
                        '&page_size=' + scope[iterator + '_page_size'] : 'page_size=' + scope[iterator + 'PageSize'];
                    Wait('start');
                    RefreshRelated({ scope: scope, set: set, iterator: iterator, url: new_url });
                };

                scope.pageIsActive = function (page, iterator) {
                    return (page === scope[iterator + '_page']) ? 'active' : '';
                };

                scope.changePageSize = function (set, iterator) {
                    // Called when a new page size is selected

                    scope[iterator + '_page'] = 1;
                    var url = scope[iterator + '_url'];

                    // Using the session cookie, keep track of user rows per page selection
                    $cookieStore.put(iterator + '_page_size', scope[iterator + '_page_size']);

                    url = url.replace(/\/\?.*$/, '/');
                    url += (scope[iterator + 'SearchParams']) ? '?' + scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + '_page_size'] :
                        '?page_size=' + scope[iterator + '_page_size'];

                    RefreshRelated({
                        scope: scope,
                        set: set,
                        iterator: iterator,
                        url: url
                    });
                };
            };
        }
    ])


    .factory('PaginateInit', ['Refresh', '$cookieStore', 'Wait',
        function (Refresh, $cookieStore, Wait) {
            return function (params) {

                var scope = params.scope,
                    list = params.list,
                    iterator = (params.iterator) ? params.iterator : list.iterator,
                    pageSize = params.pageSize,
                    mode = (params.mode) ? params.mode : null;

                scope[iterator + '_page'] = (params.page) ? params.page : 1;
                scope[iterator + '_url'] = params.url;
                scope[iterator + '_mode'] = mode;

                if (pageSize) {
                    scope[iterator + '_page_size'] = params.pageSize;
                } else if (mode === 'lookup') {
                    scope[iterator + '_page_size'] = 5;
                } else {
                    scope[iterator + '_page_size'] = 20;
                }

                scope.getPage = function (page, set, iterator) {
                    var new_url = scope[iterator + '_url'].replace(/.page\=\d+/, ''),
                        connect = (/\/$/.test(new_url)) ? '?' : '&';
                    new_url += connect + 'page=' + page;
                    new_url += (scope[iterator + 'SearchParams']) ? '&' + scope[iterator + 'SearchParams'] +
                        '&page_size=' + scope[iterator + '_page_size'] : '&page_size=' + scope[iterator + 'PageSize'];
                    Wait('start');
                    Refresh({ scope: scope, set: set, iterator: iterator, url: new_url });
                };

                scope.pageIsActive = function (page, iterator) {
                    return (page === scope[iterator + '_page']) ? 'active' : '';
                };

                scope.changePageSize = function (set, iterator, spinner) {
                    // Called whenever a new page size is selected
                    scope[iterator + '_page'] = 1;
                    var new_url = scope[iterator + '_url'].replace(/\?page_size\=\d+/, ''),
                        connect = (/\/$/.test(new_url)) ? '?' : '&';
                    new_url += (scope[iterator + 'SearchParams']) ? connect + scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + '_page_size'] :
                        connect + 'page_size=' + scope[iterator + '_page_size'];
                    if (spinner === undefined  || spinner === true) {
                        Wait('start');
                    }
                    Refresh({ scope: scope, set: set, iterator: iterator, url: new_url });
                };
            };
        }
    ]);
