/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  PaginationHelpers.js
 *
 */

angular.module('PaginationHelpers', ['Utilities', 'RefreshHelper', 'RefreshRelatedHelper'])  

    .factory('PageRangeSetup', ['Empty', function(Empty) {
    return function(params) {
        
        var scope = params.scope; 
        var count = params.count;
        var next = params.next; 
        var previous = params.previous;
        var iterator = params.iterator;

        scope[iterator + '_page'] = 1;
        scope[iterator + '_num_pages'] = Math.ceil((count / scope[iterator + '_page_size']));
        scope[iterator + '_num_pages'] = (scope[iterator + '_num_pages'] <= 0) ? 1 : scope[iterator + '_num_pages'];
        scope[iterator + '_total_rows'] = count;

        // Which page are we on?
        if ( Empty(next) && previous ) {
            // no next page, but there is a previous page
            scope[iterator + '_page'] = parseInt(previous.match(/page=\d+/)[0].replace(/page=/,'')) + 1;
        }
        else if ( next && Empty(previous) ) {
            // next page available, but no previous page
            scope[iterator + '_page'] = 1;
        }
        else if ( next && previous ) {
            // we're in between next and previous
            scope[iterator + '_page'] = parseInt(previous.match(/page=\d+/)[0].replace(/page=/,'')) + 1;
        }

        // Calc the range of up to 10 pages to show
        scope[iterator + '_page_range'] = new Array();
        var first = (scope[iterator + '_page'] > 5) ? scope[iterator + '_page'] - 5 : 1;
        if (scope[iterator + '_page'] < 6) {
            var last = (10 <= scope[iterator + '_num_pages']) ? 10 : scope[iterator + '_num_pages'];
        }
        else {
            var last = (scope[iterator + '_page'] + 4 < scope[iterator + '_num_pages']) ? 
                scope[iterator + '_page'] + 4 : scope[iterator + '_num_pages'];
        }
        for (var i=first; i <= last; i++) {
           scope[iterator + '_page_range'].push(i);
        }

        }
        }])

    .factory('RelatedPaginateInit', [ 'RefreshRelated', '$cookieStore', 'Wait',
    function(RefreshRelated, $cookieStore, Wait) {
    return function(params) {
        
        var scope = params.scope;
        var relatedSets = params.relatedSets; 
        var pageSize = (params.pageSize) ? params.pageSize : 10;

        for (var key in relatedSets){ 
            cookieSize = $cookieStore.get(relatedSets[key].iterator + '_page_size');
            scope[relatedSets[key].iterator + '_url'] = relatedSets[key].url;
            if (cookieSize) {
              // use the size found in session cookie, when available
              scope[relatedSets[key].iterator + '_page_size'] = cookieSize;
            }
            else {
              scope[relatedSets[key].iterator + '_page'] = 1;
              scope[relatedSets[key].iterator + '_page_size'] = pageSize;
            }
            console.log('setting ' + relatedSets[key].iterator + ' page_size: ' + pageSize);
        }

        scope.getPage = function(page, set, iterator) {
            var new_url = scope[iterator + '_url'].replace(/.page\=\d+/,'');
            var connect = (/\/$/.test(new_url)) ? '?' : '&';
            new_url += connect + 'page=' + page; 
            new_url += (scope[iterator + 'SearchParams']) ? '&' + scope[iterator + 'SearchParams'] + 
                '&page_size=' + scope[iterator + '_page_size' ] : 'page_size=' + scope[iterator + 'PageSize' ];
            Wait('start');
            RefreshRelated({ scope: scope, set: set, iterator: iterator, url: new_url });  
            }

        scope.pageIsActive = function(page, iterator) {
            return (page == scope[iterator + '_page']) ? 'active' : '';
            }

        scope.changePageSize = function(set, iterator) {
            // Called when a new page size is selected
            
            scope[iterator + '_page'] = 1;
            var url = scope[iterator + '_url'];

            // Using the session cookie, keep track of user rows per page selection
            $cookieStore.put(iterator + '_page_size', scope[iterator + '_page_size']);
           
            url = url.replace(/\/\?.*$/,'/');
            url += (scope[iterator + 'SearchParams']) ? '?' + scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + '_page_size' ] :
                '?page_size=' + scope[iterator + '_page_size' ];
           
            RefreshRelated({ scope: scope, set: set, iterator: iterator, url: url });  
            }

        }
        }])


    .factory('PaginateInit', [ 'Refresh', '$cookieStore', 'Wait', 
    function(Refresh, $cookieStore, Wait) {
    return function(params) {
        
        var scope = params.scope;
        var list = params.list;
        var iterator = (params.iterator) ? params.iterator : list.iterator;
        var mode = (params.mode) ? params.mode : null;
        var cookieSize = $cookieStore.get(iterator + '_page_size');
       
        scope[iterator + '_page'] = (params.page) ? params.page : 1;
        scope[iterator + '_url'] = params.url;
        scope[iterator + '_mode'] = mode;

        // Set the default page size
        if (cookieSize && mode != 'lookup') {
            // use the size found in session cookie, when available
            scope[iterator + '_page_size'] = cookieSize;
        }
        else {
           if (params.pageSize) {
               scope[iterator + '_page_size'] = params.pageSize;
           }
           else if (mode == 'lookup') {
               scope[iterator + '_page_size'] = 5;
           }
           else {
               scope[iterator + '_page_size'] = 20;
           }
        }

        scope.getPage = function(page, set, iterator) {
            var new_url = scope[iterator + '_url'].replace(/.page\=\d+/,'');
            var connect = (/\/$/.test(new_url)) ? '?' : '&';
            new_url += connect + 'page=' + page; 
            new_url += (scope[iterator + 'SearchParams']) ? '&' + scope[iterator + 'SearchParams'] + 
                '&page_size=' + scope[iterator + '_page_size' ] : 'page_size=' + scope[iterator + 'PageSize' ];
            Wait('start');
            Refresh({ scope: scope, set: set, iterator: iterator, url: new_url });  
            }
        
        scope.pageIsActive = function(page, iterator) {
            return (page == scope[iterator + '_page']) ? 'active' : '';
            }

        scope.changePageSize = function(set, iterator) {
           // Called whenever a new page size is selected
           // Using the session cookie, keep track of user rows per page selection
           $cookieStore.put(iterator + '_page_size', scope[iterator + '_page_size']);
           scope[iterator + '_page'] = 0;
           var new_url = scope[iterator + '_url'].replace(/\?page_size\=\d+/,'');
           var connect = (/\/$/.test(new_url)) ? '?' : '&';
           new_url += (scope[iterator + 'SearchParams']) ? connect + scope[iterator + 'SearchParams'] + '&page_size=' + scope[iterator + '_page_size' ] :
                connect + 'page_size=' + scope[iterator + '_page_size' ];
           Wait('start');
           Refresh({ scope: scope, set: set, iterator: iterator, url: new_url });  
           }
           
        }
        }]);