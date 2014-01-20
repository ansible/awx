/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  SearchHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  SearchInit({
 *      scope:       <scope>,
 *      set:         <model name (i.e. organizations) used in ng-repeat>
 *      url:         <default api url used to load data>
 *      list:        <list object used by ListGenerator>
 *      });   
 *
 */

angular.module('SearchHelper', ['RestServices', 'Utilities', 'RefreshHelper'])  
    .factory('SearchInit', ['Alert', 'Rest', 'Refresh', '$location', 'GetBasePath', 'Empty', '$timeout', 'Wait',
    function(Alert, Rest, Refresh, $location, GetBasePath, Empty, $timeout, Wait) {
    return function(params) {
        
        var scope = params.scope;
        var set = params.set;
        var defaultUrl = params.url;
        var list = params.list; 
        var iterator = (params.iterator) ? params.iterator : list.iterator;
        var sort_order;
        var expected_objects=0;
        var found_objects=0;
         
        if (scope.searchTimer) {
            $timeout.cancel(scope.searchTimer);
        }
        
        function setDefaults(widget) {
            // Set default values
            var modifier = (widget == undefined || widget == 1) ? '' : widget;
            scope[iterator + 'SearchField' + modifier] = '';
            scope[iterator + 'SearchFieldLabel' + modifier] = '';
            for (fld in list.fields) {
                if (list.fields[fld].searchWidget == undefined && widget == 1 || 
                    list.fields[fld].searchWidget == widget) {
                    if (list.fields[fld].key) {
                       if (list.fields[fld].sourceModel) {
                          var fka = list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
                          sort_order = (list.fields[fld].desc) ? '-' + fka : fka;
                       }
                       else {
                          sort_order = (list.fields[fld].desc) ? '-' + fld : fld; 
                       }
                       if (list.fields[fld].searchable == undefined || list.fields[fld].searchable == true) {
                          scope[iterator + 'SearchField' + modifier] = fld;
                          scope[iterator + 'SearchFieldLabel' + modifier] = list.fields[fld].label;
                       }
                       break;
                    }
                }
            }

            if (Empty(scope[iterator + 'SearchField' + modifier])) {
               // A field marked as key may not be 'searchable'. Find the first searchable field.
               for (fld in list.fields) {
                   if (list.fields[fld].searchWidget == undefined && widget == 1 || 
                       list.fields[fld].searchWidget == widget) {
                       if (list.fields[fld].searchable == undefined || list.fields[fld].searchable == true) { 
                          scope[iterator + 'SearchField' + modifier] = fld;
                          scope[iterator + 'SearchFieldLabel' + modifier] = list.fields[fld].label;
                          break;
                       }
                   }
               }
            }

            scope[iterator + 'SearchType' + modifier] = 'icontains';
            scope[iterator + 'SearchTypeLabel' + modifier] = 'Contains';
            scope[iterator + 'SearchParams' + modifier] = '';
            scope[iterator + 'SearchValue' + modifier] = '';
            scope[iterator + 'SelectShow' + modifier] = false;   // show/hide the Select
            scope[iterator + 'HideSearchType' + modifier] = false;
            scope[iterator + 'InputDisable' + modifier] = false;
            scope[iterator + 'ExtraParms' + modifier] = '';
            scope[iterator + 'ShowStartBtn' + modifier] = true;
            scope[iterator + 'HideAllStartBtn' + modifier] = false;
            
            if (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder) {
                if (scope[list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder]) {
                    // if set to a scope variable
                    scope[iterator + 'SearchPlaceholder' + modifier] = scope[list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder];
                }
                else {
                    // Set to a string value in the list definition
                    scope[iterator + 'SearchPlaceholder' + modifier] = list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder;
                }  
            }
            else {
                // Default value
                scope[iterator + 'SearchPlaceholder' + modifier] = 'Search';
            }
            
            scope[iterator + 'InputDisable' + modifier] = 
                (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                    list.fields[scope[iterator + 'SearchField' + modifier]].searchObject == 'all') ? true : false;

            var f = scope[iterator + 'SearchField' + modifier];
            if (list.fields[f]) {
                if ( list.fields[f].searchType && (list.fields[f].searchType == 'boolean' 
                     || list.fields[f].searchType == 'select') ) {
                    scope[iterator + 'SelectShow' + modifier] = true;
                    scope[iterator + 'SearchSelectOpts' + modifier] = list.fields[f].searchOptions;
                }
                if (list.fields[f].searchType && list.fields[f].searchType == 'int') {
                    scope[iterator + 'HideSearchType' + modifier] = true;   
                }
                if (list.fields[f].searchType && list.fields[f].searchType == 'gtzero') {
                    scope[iterator + 'InputHide' + modifier] = true;
                }
            }
            }
        
        // Set default values for each search widget on the page
        var widgets = (list.searchWidgets) ? list.searchWidgets : 1;
        for (var i=1; i <= widgets; i++) {
            var modifier = (i == 1) ? '' : i;
            if ( $('#search-widget-container' + modifier) ) {
                setDefaults(i);
            }
        }
       
        // Functions to handle search widget changes
        scope.setSearchField = function(iterator, fld, label, widget) {
           
            var modifier = (widget == undefined || widget == 1) ? '' : widget;
            scope[iterator + 'SearchFieldLabel' + modifier] = label;
            scope[iterator + 'SearchField' + modifier] = fld;
            scope[iterator + 'SearchValue' + modifier] = '';
            scope[iterator + 'SelectShow' + modifier] = false;
            scope[iterator + 'HideSearchType' + modifier] = false;
            scope[iterator + 'InputHide' + modifier] = false;
            scope[iterator + 'SearchType' + modifier] = 'icontains';
            scope[iterator + 'InputDisable' + modifier] = (list.fields[fld].searchObject == 'all') ? true : false;
            scope[iterator + 'ShowStartBtn' + modifier] = true;
            
            if (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder) {
                if (scope[list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder]) {
                    // if set to a scope variable
                    scope[iterator + 'SearchPlaceholder' + modifier] = scope[list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder];
                }
                else {
                    // Set to a string value in the list definition
                    scope[iterator + 'SearchPlaceholder' + modifier] = list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder;
                }  
            }
            else {
                // Default value
                scope[iterator + 'SearchPlaceholder' + modifier] = 'Search';
            }

            if (list.fields[fld].searchType && list.fields[fld].searchType == 'gtzero') {
                scope[iterator + "InputDisable" + modifier] = true;
                scope[iterator + 'ShowStartBtn' + modifier] = false;
                scope.search(iterator);
            }
            else if (list.fields[fld].searchSingleValue){
                // Query a specific attribute for one specific value
                // searchSingleValue: true
                // searchType: 'boolean|int|etc.'
                // searchValue: < value to match for boolean use 'true'|'false' >
                scope[iterator + 'InputDisable' + modifier] = true;
                scope[iterator + "SearchValue" + modifier] = list.fields[fld].searchValue;
                // For boolean type, SearchValue must be an object
                if (list.fields[fld].searchType == 'boolean' && list.fields[fld].searchValue == 'true') {
                   scope[iterator + "SearchSelectValue" + modifier] = { value: 1 }; 
                }
                else if (list.fields[fld].searchType == 'boolean' && list.fields[fld].searchValue == 'false') {
                   scope[iterator + "SearchSelectValue" + modifier] = { value: 0 };
                }
                else {
                   scope[iterator + "SearchSelectValue" + modifier] = { value: list.fields[fld].searchValue };
                }
                scope[iterator + 'ShowStartBtn' + modifier] = false;
            }
            else if (list.fields[fld].searchType == 'in') {
                scope[iterator + "SearchType" + modifier] = 'in';
                scope[iterator + "SearchValue" + modifier] = list.fields[fld].searchValue;
                scope[iterator + "InputDisable" + modifier] = true;
                scope[iterator + 'ShowStartBtn' + modifier] = false;
            }
            else if (list.fields[fld].searchType && (list.fields[fld].searchType == 'boolean' 
                || list.fields[fld].searchType == 'select' || list.fields[fld].searchType == 'select_or')) {
                scope[iterator + 'SelectShow' + modifier] = true;
                scope[iterator + 'SearchSelectOpts' + modifier] = list.fields[fld].searchOptions;
            }
            else if (list.fields[fld].searchType && list.fields[fld].searchType == 'int') {
                //scope[iterator + 'HideSearchType' + modifier] = true;
                scope[iterator + 'SearchType' + modifier] = 'int';
            }
            else if (list.fields[fld].searchType && list.fields[fld].searchType == 'isnull') {
                scope[iterator + 'SearchType' + modifier] = 'isnull';
                scope[iterator + 'InputDisable' + modifier] = true;
                scope[iterator + 'SearchValue' + modifier] = 'true';
                scope[iterator + 'ShowStartBtn' + modifier] = false;
            }
            
            scope.search(iterator);   
            
            }

        scope.resetSearch = function(iterator) {
            // Respdond to click of reset button
            var widgets = (list.searchWidgets) ? list.searchWidgets : 1;
            for (var i=1; i <= widgets; i++) {
                // Clear each search widget
                setDefaults(i);
            }
            // Force removal of search keys from the URL
            window.location = '/#' + $location.path();
            scope.search(iterator);
            }
        
        if (scope.removeDoSearch) {
            scope.removeDoSearch();
        }
        scope.removeDoSearch = scope.$on('doSearch', function(e, iterator, page, load, spin) {
            //
            // Execute the search
            //
            //scope[iterator + 'SearchSpin'] = (spin == undefined || spin == true) ? true : false;
            scope[iterator + 'Loading'] = (load == undefined || load == true) ? true : false;
            var url = defaultUrl;

            //finalize and execute the query
            scope[iterator + 'Page'] = (page) ? parseInt(page) - 1 : 0;
            if (/\/$/.test(url)) {
                url += '?' + scope[iterator + 'SearchParams'];
            }
            else {
                url += '&' + scope[iterator + 'SearchParams'];
            }
            url = url.replace(/\&\&/,'&');
            url += (scope[iterator + 'PageSize']) ? '&page_size=' + scope[iterator + 'PageSize'] : "";
            if (page) {
                url += '&page=' + page;
            }
            if (scope[iterator + 'ExtraParms']) {
                url += scope[iterator + 'ExtraParms'];
            }
            Refresh({ scope: scope, set: set, iterator: iterator, url: url });
            });
        
        /*
        if (scope.removeFoundObject) {
           scope.removeFoundObject();
        }
        scope.removeFoundObject = scope.$on('foundObject', function(e, iterator, page, load, spin, widget, pk) {
            found_objects++; 
            // Add new criteria to search params
            var modifier = (widget == 1) ? '' : widget;
            var objs = list.fields[scope[iterator + 'SearchField' + modifier]].searchObject;
            var o = (objs == 'inventories') ? 'inventory' : objs.replace(/s$/,'');
            var searchFld = list.fields[scope[iterator + 'SearchField' + modifier]].searchField;
            scope[iterator + 'SearchParams'] += '&' + searchFld + '__icontains=' + o;
            if (!Empty(pk)) {
               scope[iterator + 'SearchParams'] += '&' + searchFld + '_id__in=' + pk;
            }
            // Move to the next phase once all object types are processed
            if (found_objects == expected_objects) {
               scope.$emit('prepareSearch2', iterator, page, load, spin);
            }
            });
        */

        /*if (scope.removeResultWarning) {
            scope.removeResultWarning();
        }
        scope.removeResultWarning = scope.$on('resultWarning', function(e, objs, length) {
            // Alert the user that the # of objects was greater than 30
            var label = (objs == 'inventory') ? 'inventories' : objs.replace(/s$/,'');
            Alert('Warning', 'The number of matching ' + label + ' was too large. We limited your search to the first 30.', 'alert-info');
            });
        */

        if (scope.removePrepareSearch) {
            scope.removePrepareSearch();
        }
        scope.removePrepareSearch = scope.$on('prepareSearch', function(e, iterator, page, load, spin) {
            //
            // Start building the search key/value pairs. This will process each search widget, if the
            // selected field is an object type (used on activity stream).
            //
            Wait('start');
            scope[iterator + 'SearchParams'] = '';
            var widgets = (list.searchWidgets) ? list.searchWidgets : 1;
            var modifier;
            
            // Determine how many object values we're dealing with.
            /*
            expected_objects = 0;
            found_objects = 0;
            for (var i=1; i <= widgets; i++) {
                modifier = (i == 1) ? '' : i;
                scope[iterator + 'HoldInput' + modifier] = true; //Block any input until we're done. Refresh.js will flip this back.
                if ($('#search-widget-container' + modifier) &&
                    list.fields[scope[iterator + 'SearchField' + modifier]] &&
                    list.fields[scope[iterator + 'SearchField' + modifier]].searchObject &&
                    list.fields[scope[iterator + 'SearchField'  + modifier]].searchObject !== 'all') {
                   expected_objects++;
                }
            }
            */
            
            for (var i=1; i <= widgets; i++) {
                var modifier = (i == 1) ? '' : i;
                if ( $('#search-widget-container' + modifier) ) {
                    if (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                        list.fields[scope[iterator + 'SearchField' + modifier]].searchObject) {
                        // Search field of object type
                        if (list.fields[scope[iterator + 'SearchField'  + modifier]].searchObject !== 'all') {
                            // An object type is selected
                            scope[iterator + 'HideAllStartBtn' + modifier] = false;
                            if (scope[iterator + 'SearchValue' + modifier]) {
                                // A search value was entered
                                scope[iterator + 'ShowStartBtn' + modifier] = false;
                                scope[iterator + 'SearchParams'] += '&' +
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchObject + 
                                    '__name__icontains=' +
                                    scope[iterator + 'SearchValue' + modifier];

                                //var objUrl = GetBasePath('base') + objs + '/?name__icontains=' + scope[iterator + 'SearchValue' + modifier];
                                /*
                                Rest.setUrl(objUrl);
                                Rest.setHeader({ widget: i });
                                Rest.setHeader({ object: objs });
                                Rest.get()
                                    .success( function(data, status, headers, config) {
                                        var pk='';
                                        //limit result set to 30
                                        var len = (data.results.length > 30) ? 30 : data.results.length;
                                        for (var j=0; j < len; j++) {
                                            pk += "," + data.results[j].id;
                                        } 
                                        pk = pk.replace(/^\,/,'');
                                        scope.$emit('foundObject', iterator, page, load, spin, config.headers['widget'], pk);
                                        if (data.results.length > 30) {
                                            scope.$emit('resultWarning', config.headers['object'], data.results.length);
                                        }
                                        })
                                   .error( function(data, status, headers, config) {
                                        Wait('stop');
                                        ProcessErrors(scope, data, status, null,
                                            { hdr: 'Error!', msg: 'Retrieving list of ' + objs + ' where name contains: ' + scope[iterator + 'SearchValue' + modifier] +
                                            ' GET returned status: ' + status });
                                        });
                                */
                            }    
                            else {
                                // Search value is empty
                                scope[iterator + 'ShowStartBtn' + modifier] = true;
                                scope[iterator + 'SearchParams'] += '&' +
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchField + 
                                    '=' + list.fields[scope[iterator + 'SearchField' + modifier]].searchObject;
                                //scope.$emit('foundObject', iterator, page, load, spin, i, null);  
                            }
                        }
                        else {
                            // Object Type set to All
                            scope[iterator + 'HideAllStartBtn' + modifier] = true;
                        }
                    }
                }
            }
            scope.$emit('prepareSearch2', iterator, page, load, spin);
            //if (expected_objects == 0) {
                // No search widgets contain objects
            //    scope.$emit('prepareSearch2', iterator, page, load, spin);
            //}
            });
        
        if (scope.removePrepareSearch2) {
            scope.removePrepareSearch2();
        }
        scope.removePrepareSearch2 = scope.$on('prepareSearch2', function(e, iterator, page, load, spin) {  
            // Continue building the search by examining the remaining search widgets. If we're looking at activity_stream,
            // there's more than one.
            var widgets = (list.searchWidgets) ? list.searchWidgets : 1;
            var modifier;
            for (var i=1; i <= widgets; i++) {
                modifier = (i == 1) ? '' : i;
                scope[iterator + 'HoldInput' + modifier] = true; 
                if ($('#search-widget-container' + modifier) && 
                    list.fields[scope[iterator + 'SearchField' + modifier]] &&
                    !list.fields[scope[iterator + 'SearchField' + modifier]].searchObject) {
                    
                    // if the search widget exists and its value is not an object, add its parameters to the query

                    if (scope[iterator + 'SearchValue' + modifier]) {
                        // if user typed a value in the input box, show the reset link
                        scope[iterator + 'ShowStartBtn' + modifier] = false;
                    }
                    
                    if ( (!scope[iterator + 'SelectShow' + modifier] && !Empty(scope[iterator + 'SearchValue' + modifier])) ||
                           (scope[iterator + 'SelectShow' + modifier] && scope[iterator + 'SearchSelectValue' + modifier]) || 
                           (list.fields[scope[iterator + 'SearchField' + modifier]] && 
                            list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'gtzero') ) {
                        if (list.fields[scope[iterator + 'SearchField' + modifier]].searchField) {
                            scope[iterator + 'SearchParams'] += '&' + list.fields[scope[iterator + 'SearchField' + modifier]].searchField + '__'; 
                        }
                        else if (list.fields[scope[iterator + 'SearchField' + modifier]].sourceModel) {
                            // handle fields whose source is a related model e.g. inventories.organization
                            scope[iterator + 'SearchParams'] += '&' + list.fields[scope[iterator + 'SearchField' + modifier]].sourceModel + '__' + 
                            list.fields[scope[iterator + 'SearchField' + modifier]].sourceField + '__';
                        }
                        else if ( (list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'select') && 
                                  (scope[iterator + 'SearchSelectValue' + modifier].value == '' || 
                                      scope[iterator + 'SearchSelectValue' + modifier].value == null) ) {
                            scope[iterator + 'SearchParams'] += '&' + scope[iterator + 'SearchField' + modifier] + '__';
                        }
                        else {
                            scope[iterator + 'SearchParams'] += '&' + scope[iterator + 'SearchField' + modifier] + '__'; 
                        }
                        
                        if ( list.fields[scope[iterator + 'SearchField' + modifier]].searchType && 
                             (list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'int' || 
                              list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'boolean' ) ) {
                            scope[iterator + 'SearchParams'] += 'int=';  
                        }
                        else if ( list.fields[scope[iterator + 'SearchField' + modifier]].searchType && 
                                  list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'gtzero' ) {
                            scope[iterator + 'SearchParams'] += 'gt=0'; 
                        }
                        else if ( (list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'select') && 
                                  (scope[iterator + 'SearchSelectValue' + modifier].value == '' || 
                                      scope[iterator + 'SearchSelectValue' + modifier].value == null) ) {
                            scope[iterator + 'SearchParams'] += 'iexact=';
                        }
                        /*else if ( (list.fields[scope[iterator + 'SearchField' + modifier]].searchType && 
                                  (list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'or')) ) {
                            scope[iterator + 'SearchParams'] = ''; //start over
                            var val = scope[iterator + 'SearchValue' + modifier];
                            for (var k=0; k < list.fields[scope[iterator + 'SearchField' + modifier]].searchFields.length; k++) {
                                scope[iterator + 'SearchParams'] += '&or__' +
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchFields[k] +
                                    '__icontains=' + escape(val); 
                            }
                            scope[iterator + 'SearchParams'].replace(/^\&/,'');     
                        }*/
                        else {
                            scope[iterator + 'SearchParams'] += scope[iterator + 'SearchType' + modifier] + '='; 
                        }             
                        
                        if ( list.fields[scope[iterator + 'SearchField' + modifier]].searchType && 
                             (list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'boolean' 
                                 || list.fields[scope[iterator + 'SearchField' + modifier]].searchType == 'select') ) { 
                            scope[iterator + 'SearchParams'] += scope[iterator + 'SearchSelectValue' + modifier].value;
                        }
                        else {
                            if ( (!list.fields[scope[iterator + 'SearchField' + modifier]].searchType) ||
                                (list.fields[scope[iterator + 'SearchField' + modifier]].searchType && 
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchType !== 'or' &&
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchType !== 'gtzero') ) {
                                scope[iterator + 'SearchParams'] += escape(scope[iterator + 'SearchValue' + modifier]);
                            }
                        }
                    }
                }
            }

            if ( (iterator == 'inventory' && scope.inventoryFailureFilter) ||
                (iterator == 'host' && scope.hostFailureFilter) ) {
                //Things that bypass the search widget. Should go back and add a second widget possibly on
                //inventory pages and eliminate this
                scope[iterator + 'SearchParams'] += '&has_active_failures=true';
            }
            
            if (sort_order) {
                scope[iterator + 'SearchParams'] += (scope[iterator + 'SearchParams']) ? '&' : '';
                scope[iterator + 'SearchParams'] += 'order_by=' + escape(sort_order);
            }

            scope.$emit('doSearch', iterator, page, load, spin);
        });

        scope.startSearch = function(e,iterator) {
           // If use clicks enter while on input field, start the search
           if (e.keyCode == 13) {
              scope.search(iterator);
           }
           }

        scope.search = function(iterator, page, load, spin) {
           // Called to initiate a searh. 
           // Page is optional. Added to accomodate back function on Job Events detail. 
           // Spin optional -set to false if spin not desired.
           // Load optional -set to false if loading message not desired
           scope.$emit('prepareSearch', iterator, page, load, spin); 
           }

        
        scope.sort = function(fld) {
            // reset sort icons back to 'icon-sort' on all columns
            // except the one clicked
            $('.list-header').each(function(index) {
                if ($(this).attr('id') != fld + '-header') {
                   var icon = $(this).find('i');
                   icon.attr('class','fa fa-sort');
                }
                });
 
            // Toggle the icon for the clicked column
            // and set the sort direction  
            var icon = $('#' + fld + '-header i');
            var direction = '';
            if (icon.hasClass('fa-sort')) {
               icon.removeClass('fa-sort');
               icon.addClass('fa-sort-up');
            }
            else if (icon.hasClass('fa-sort-up')) {
               icon.removeClass('fa-sort-up');
               icon.addClass('fa-sort-down');
               direction = '-';
            }
            else if (icon.hasClass('fa-sort-down')) {
               icon.removeClass('fa-sort-down');
               icon.addClass('fa-sort-up');
            }

            // Set the sorder order value and call the API to refresh the list with the new order
            if (list.fields[fld].searchField) {
               sort_order = direction + list.fields[fld].searchField;
            }
            else if (list.fields[fld].sortField) {
               sort_order = direction + list.fields[fld].sortField;
            }
            else {
               if (list.fields[fld].sourceModel) {
                  sort_order = direction + list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
               }
               else {
                  sort_order = direction + fld; 
               }
            }
            scope.search(list.iterator);
            }

        // Call after modal dialogs to remove any lingering callbacks
        scope.searchCleanup = function() {
            scope.removeDoSearch();
            scope.removePrepareSearch(); 
            scope.removePrepareSearch2();
            }

        }
        }]);
