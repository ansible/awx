/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
    /**
 * @ngdoc function
 * @name helpers.function:refresh
 * @description
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


export default
    angular.module('RefreshHelper', ['RestServices', 'Utilities', 'PaginationHelpers'])
        .factory('Refresh', ['$location', 'ProcessErrors', 'Rest', 'Wait', 'Empty', 'PageRangeSetup',
            function ($location, ProcessErrors, Rest, Wait, Empty, PageRangeSetup) {
                return function (params) {

                    var scope = params.scope,
                        set = params.set,
                        iterator = params.iterator,
                        url = params.url,
                        deferWaitStop = params.deferWaitStop;

                    if ($location.$$url.split("/")[2] && !scope.getNewPage) {
                        var id = $location.$$url.split("/")[2];
                        Rest.setUrl(params.url.split("?")[0] + "?id=" + id);
                        Rest.get()
                            .then(function (data) {
                                var name = data.data.results[0].name;
                                Rest.setUrl(params.url.split("?")[0] + "?name__lte=" + name);
                                Rest.get()
                                    .then(function (data) {
                                        var currentPage = Math.ceil(data.data.count/scope[iterator + '_page_size']);
                                        scope[iterator + '_page'] = currentPage;
                                        params.url = params.url + "&page=" + currentPage;
                                        scope.current_url = params.url;
                                        Rest.setUrl(params.url);
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
                                                scope[iterator + 'HidePaginator'] = false;
                                                if (!deferWaitStop) {
                                                    Wait('stop');
                                                }
                                                scope.$emit('PostRefresh', set);
                                            })
                                            .error(function (data, status) {
                                                scope[iterator + 'HoldInput'] = false;
                                                ProcessErrors(scope, data, status, null, {
                                                    hdr: 'Error!',
                                                    msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status
                                                });
                                            });
                                    });
                            });
                    } else {
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
                                scope[iterator + 'HidePaginator'] = false;
                                if (!deferWaitStop) {
                                    Wait('stop');
                                }
                                scope.$emit('PostRefresh', set);
                            })
                            .error(function (data, status) {
                                scope[iterator + 'HoldInput'] = false;
                                ProcessErrors(scope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to retrieve ' + set + '. GET returned status: ' + status
                                });
                            });
                        scope.getNewPage = false;
                    }
                };


            }
        ]);
