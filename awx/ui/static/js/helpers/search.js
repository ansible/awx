/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
    /**
 * @ngdoc function
 * @name helpers.function:search
 * @description
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

'use strict';

angular.module('SearchHelper', ['RestServices', 'Utilities', 'RefreshHelper'])

.factory('SearchInit', ['Alert', 'Rest', 'Refresh', '$location', 'GetBasePath', 'Empty', '$timeout', 'Wait', 'Store',
    function (Alert, Rest, Refresh, $location, GetBasePath, Empty, $timeout, Wait, Store) {
        return function (params) {

            var scope = params.scope,
                set = params.set,
                defaultUrl = params.url,
                list = params.list,
                iterator = (params.iterator) ? params.iterator : list.iterator,
                setWidgets = (params.setWidgets === false) ? false : true,
                sort_order = params.sort_order || '',
                widgets, i, modifier;


            // add 'selected' class to the selected li element
            function setSelectedItem(iterator, label, modifier) {
                // add 'selected' class to the selected li element
                $('#' + iterator + 'SearchDropdown' + modifier + ' li').each(function() {
                    $(this).removeClass('selected');
                    var link = $(this).find('a');
                    if (label === link.text()) {
                        $(this).addClass('selected');
                    }
                });
            }

            function setDefaults(widget) {
                // Set default values
                var f, fld, fka, modifier;
                modifier = (widget === undefined || widget === 1) ? '' : widget;
                scope[iterator + 'SearchField' + modifier] = '';
                scope[iterator + 'SearchFieldLabel' + modifier] = '';
                for (fld in list.fields) {
                    if (list.fields[fld].searchWidget === undefined && widget === 1 ||
                        list.fields[fld].searchWidget === widget) {
                        if (list.fields[fld].key) {
                            if (list.fields[fld].sourceModel) {
                                fka = list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
                                sort_order = (list.fields[fld].desc) ? '-' + fka : fka;
                            } else {
                                sort_order = (list.fields[fld].desc) ? '-' + fld : fld;
                            }
                            if (list.fields[fld].searchable === undefined || list.fields[fld].searchable === true) {
                                scope[iterator + 'SearchField' + modifier] = fld;
                                scope[iterator + 'SearchFieldLabel' + modifier] = list.fields[fld].label;
                            }
                            break;
                        }
                    }
                }

                // Default the search field to 'defaultSearchField', if one exists
                for (fld in list.fields) {
                    if (list.fields[fld].searchWidget === undefined && widget === 1 ||
                        list.fields[fld].searchWidget === widget) {
                        if (list.fields[fld].defaultSearchField) {
                            scope[iterator + 'SearchField' + modifier] = fld;
                            scope[iterator + 'SearchFieldLabel' + modifier] = list.fields[fld].label;
                        }
                    }
                }

                // A field marked as key may not be 'searchable', and there might not be a 'defaultSearchField',
                // so find the first searchable field.
                if (Empty(scope[iterator + 'SearchField' + modifier])) {
                    for (fld in list.fields) {
                        if (list.fields[fld].searchWidget === undefined && widget === 1 ||
                            list.fields[fld].searchWidget === widget) {
                            if (list.fields[fld].searchable === undefined || list.fields[fld].searchable === true) {
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
                scope[iterator + 'SelectShow' + modifier] = false; // show/hide the Select
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
                    } else {
                        // Set to a string value in the list definition
                        scope[iterator + 'SearchPlaceholder' + modifier] = list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder;
                    }
                } else {
                    // Default value
                    scope[iterator + 'SearchPlaceholder' + modifier] = 'Search';
                }

                scope[iterator + 'InputDisable' + modifier] =
                    (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                    list.fields[scope[iterator + 'SearchField' + modifier]].searchObject === 'all') ? true : false;

                f = scope[iterator + 'SearchField' + modifier];
                if (list.fields[f]) {
                    if (list.fields[f].searchType && (list.fields[f].searchType === 'boolean' ||
                        list.fields[f].searchType === 'select')) {
                        scope[iterator + 'SelectShow' + modifier] = true;
                        scope[iterator + 'SearchSelectOpts' + modifier] = list.fields[f].searchOptions;
                    }
                    if (list.fields[f].searchType && list.fields[f].searchType === 'int') {
                        scope[iterator + 'HideSearchType' + modifier] = true;
                    }
                    if (list.fields[f].searchType && list.fields[f].searchType === 'gtzero') {
                        scope[iterator + 'InputHide' + modifier] = true;
                    }
                }

                setSelectedItem(iterator, scope[iterator + 'SearchFieldLabel' + modifier], modifier);
            }

            if (setWidgets) {
                // Set default values for each search widget on the page
                widgets = (list.searchWidgets) ? list.searchWidgets : 1;
                for (i = 1; i <= widgets; i++) {
                    modifier = (i === 1) ? '' : i;
                    if ($('#search-widget-container' + modifier)) {
                        setDefaults(i);
                    }
                }
            }

            scope[iterator + '_current_search_params'] = {
                set: set,
                defaultUrl: defaultUrl,
                list: list,
                iterator: iterator,
                sort_order: sort_order
            };

            Store(iterator + '_current_search_params', scope[iterator + '_current_search_params']);
            Store('CurrentSearchParams', scope[iterator + '_current_search_params']); // Keeping this around for activity stream


            // Functions to handle search widget changes
            scope.setSearchField = function (iterator, fld, label, widget) {

                var modifier = (widget === undefined || widget === 1) ? '' : widget;
                scope[iterator + 'SearchFieldLabel' + modifier] = label;
                scope[iterator + 'SearchField' + modifier] = fld;
                scope[iterator + 'SearchValue' + modifier] = '';
                scope[iterator + 'SelectShow' + modifier] = false;
                scope[iterator + 'HideSearchType' + modifier] = false;
                scope[iterator + 'InputHide' + modifier] = false;
                scope[iterator + 'SearchType' + modifier] = 'icontains';
                scope[iterator + 'InputDisable' + modifier] = (list.fields[fld].searchObject === 'all') ? true : false;
                scope[iterator + 'ShowStartBtn' + modifier] = true;

                if (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                    list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder) {
                    if (scope[list.fields[scope[iterator + 'SearchField' + modifier]].searchPlaceholder]) {
                        // if set to a scope variable
                        scope[iterator + 'SearchPlaceholder' + modifier] = scope[list.fields[scope[iterator + 'SearchField' +
                            modifier]].searchPlaceholder];
                    } else {
                        // Set to a string value in the list definition
                        scope[iterator + 'SearchPlaceholder' + modifier] = list.fields[scope[iterator + 'SearchField' +
                            modifier]].searchPlaceholder;
                    }
                } else {
                    // Default value
                    scope[iterator + 'SearchPlaceholder' + modifier] = 'Search';
                }

                if (list.fields[fld].searchType && list.fields[fld].searchType === 'gtzero') {
                    scope[iterator + "InputDisable" + modifier] = true;
                    scope[iterator + 'ShowStartBtn' + modifier] = false;
                    scope.search(iterator);
                } else if (list.fields[fld].searchSingleValue) {
                    // Query a specific attribute for one specific value
                    // searchSingleValue: true
                    // searchType: 'boolean|int|etc.'
                    // searchValue: < value to match for boolean use 'true'|'false' >
                    scope[iterator + 'InputDisable' + modifier] = true;
                    scope[iterator + "SearchValue" + modifier] = list.fields[fld].searchValue;
                    // For boolean type, SearchValue must be an object
                    if (list.fields[fld].searchType === 'boolean' && list.fields[fld].searchValue === 'true') {
                        scope[iterator + "SearchSelectValue" + modifier] = {
                            value: 1
                        };
                    } else if (list.fields[fld].searchType === 'boolean' && list.fields[fld].searchValue === 'false') {
                        scope[iterator + "SearchSelectValue" + modifier] = {
                            value: 0
                        };
                    } else {
                        scope[iterator + "SearchSelectValue" + modifier] = {
                            value: list.fields[fld].searchValue
                        };
                    }
                    scope[iterator + 'ShowStartBtn' + modifier] = false;
                } else if (list.fields[fld].searchType === 'in') {
                    scope[iterator + "SearchType" + modifier] = 'in';
                    scope[iterator + "SearchValue" + modifier] = list.fields[fld].searchValue;
                    scope[iterator + "InputDisable" + modifier] = true;
                    scope[iterator + 'ShowStartBtn' + modifier] = false;
                } else if (list.fields[fld].searchType && (list.fields[fld].searchType === 'boolean' ||
                    list.fields[fld].searchType === 'select' || list.fields[fld].searchType === 'select_or')) {
                    scope[iterator + 'SelectShow' + modifier] = true;
                    scope[iterator + 'SearchSelectOpts' + modifier] = list.fields[fld].searchOptions;
                    scope[iterator + 'SearchType' + modifier] = '';
                } else if (list.fields[fld].searchType && list.fields[fld].searchType === 'int') {
                    //scope[iterator + 'HideSearchType' + modifier] = true;
                    scope[iterator + 'SearchType' + modifier] = 'int';
                } else if (list.fields[fld].searchType && list.fields[fld].searchType === 'isnull') {
                    scope[iterator + 'SearchType' + modifier] = 'isnull';
                    scope[iterator + 'InputDisable' + modifier] = true;
                    scope[iterator + 'SearchValue' + modifier] = 'true';
                    scope[iterator + 'ShowStartBtn' + modifier] = false;
                }

                setSelectedItem(iterator, label, modifier);

                scope.search(iterator);
            };

            scope.resetSearch = function (iterator) {
                // Respdond to click of reset button
                var i,
                    widgets = (list.searchWidgets) ? list.searchWidgets : 1;

                for (i = 1; i <= widgets; i++) {
                    // Clear each search widget
                    setDefaults(i);
                }
                // Force removal of search keys from the URL
                window.location = '/#' + $location.path();
                scope.search(iterator);
            };

            if (scope.removeDoSearch) {
                scope.removeDoSearch();
            }
            scope.removeDoSearch = scope.$on('doSearch', function (e, iterator, page, load, calcOnly, deferWaitStop) {
                //
                // Execute the search
                //
                var url = (calcOnly) ? '' : defaultUrl,
                    connect;

                if (!calcOnly) {
                    scope[iterator + 'Loading'] = (load === undefined || load === true) ? true : false;
                    scope[iterator + 'Page'] = (page) ? parseInt(page) - 1 : 0;
                }

                //finalize and execute the query
                if (scope[iterator + 'SearchParams']) {
                    if (/\/$/.test(url)) {
                        url += '?' + scope[iterator + 'SearchParams'];
                    } else {
                        url += '&' + scope[iterator + 'SearchParams'];
                    }
                }
                connect = (/\/$/.test(url)) ? '?' : '&';
                url += (scope[iterator + '_page_size']) ? connect + 'page_size=' + scope[iterator + '_page_size'] : "";
                if (page) {
                    connect = (/\/$/.test(url)) ? '?' : '&';
                    url += connect + 'page=' + page;
                }
                if (scope[iterator + 'ExtraParms']) {
                    connect = (/\/$/.test(url)) ? '?' : '&';
                    url += connect + scope[iterator + 'ExtraParms'];
                }
                url = url.replace(/\&\&/g, '&').replace(/\?\&/,'?');
                if (calcOnly) {
                    scope.$emit('searchParamsReady', url);
                }
                else if (defaultUrl && !/undefined/.test(url)) {
                    Refresh({
                        scope: scope,
                        set: set,
                        iterator: iterator,
                        url: url,
                        deferWaitStop: deferWaitStop
                    });
                }
                e.stopPropagation();
            });


            if (scope.removePrepareSearch) {
                scope.removePrepareSearch();
            }
            scope.removePrepareSearch = scope.$on('prepareSearch', function (e, iterator, page, load, calcOnly, deferWaitStop, spinner) {
                //
                // Start building the search key/value pairs. This will process each search widget, if the
                // selected field is an object type (used on activity stream).
                //
                if (spinner) {
                    Wait('start');
                }
                scope[iterator + 'SearchParams'] = '';
                var i, modifier,
                    widgets = (list.searchWidgets) ? list.searchWidgets : 1;

                for (i = 1; i <= widgets; i++) {
                    modifier = (i === 1) ? '' : i;
                    if ($('#search-widget-container' + modifier)) {
                        if (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                            list.fields[scope[iterator + 'SearchField' + modifier]].searchObject) {
                            // Search field of object type
                            if (list.fields[scope[iterator + 'SearchField' + modifier]].searchObject !== 'all') {
                                // An object type is selected
                                scope[iterator + 'HideAllStartBtn' + modifier] = false;
                                if (scope[iterator + 'SearchValue' + modifier]) {
                                    // A search value was entered
                                    scope[iterator + 'ShowStartBtn' + modifier] = false;
                                    if (list.fields[scope[iterator + 'SearchField' + modifier]].searchOnID) {
                                        scope[iterator + 'SearchParams'] += '&' +
                                            list.fields[scope[iterator + 'SearchField' + modifier]].searchObject +
                                            '__id=' + scope[iterator + 'SearchValue' + modifier];
                                    } else {
                                        scope[iterator + 'SearchParams'] += '&' +
                                            list.fields[scope[iterator + 'SearchField' + modifier]].searchObject +
                                            ( (list.fields[scope[iterator + 'SearchField' + modifier]].searchObject === 'user') ? '__username__icontains=' : '__name__icontains=' ) +
                                            scope[iterator + 'SearchValue' + modifier];
                                    }
                                } else {
                                    // Search value is empty
                                    scope[iterator + 'ShowStartBtn' + modifier] = true;
                                    scope[iterator + 'SearchParams'] += '&' +
                                        list.fields[scope[iterator + 'SearchField' + modifier]].searchField +
                                        '=' + list.fields[scope[iterator + 'SearchField' + modifier]].searchObject;
                                }
                            } else {
                                // Object Type set to All
                                scope[iterator + 'HideAllStartBtn' + modifier] = true;
                            }
                        }
                    }
                }
                e.stopPropagation();
                scope.$emit('prepareSearch2', iterator, page, load, calcOnly, deferWaitStop);

            });

            if (scope.removePrepareSearch2) {
                scope.removePrepareSearch2();
            }
            scope.removePrepareSearch2 = scope.$on('prepareSearch2', function (e, iterator, page, load, calcOnly, deferWaitStop) {
                // Continue building the search by examining the remaining search widgets. If we're looking at activity_stream,
                // there's more than one.
                var i, modifier,
                    widgets = (list.searchWidgets) ? list.searchWidgets : 1;

                for (i = 1; i <= widgets; i++) {
                    modifier = (i === 1) ? '' : i;
                    scope[iterator + 'HoldInput' + modifier] = true;
                    if ($('#search-widget-container' + modifier) &&
                        list.fields[scope[iterator + 'SearchField' + modifier]] && !list.fields[scope[iterator + 'SearchField' + modifier]].searchObject) {

                        // if the search widget exists and its value is not an object, add its parameters to the query

                        if (scope[iterator + 'SearchValue' + modifier]) {
                            // if user typed a value in the input box, show the reset link
                            scope[iterator + 'ShowStartBtn' + modifier] = false;
                        } else {
                            scope[iterator + 'ShowStartBtn' + modifier] = true;
                        }
                        if ((!scope[iterator + 'SelectShow' + modifier] && !Empty(scope[iterator + 'SearchValue' + modifier])) ||
                            (scope[iterator + 'SelectShow' + modifier] && scope[iterator + 'SearchSelectValue' + modifier]) ||
                            (list.fields[scope[iterator + 'SearchField' + modifier]] &&
                                list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'gtzero')) {
                            if (list.fields[scope[iterator + 'SearchField' + modifier]].searchField) {
                                scope[iterator + 'SearchParams'] += '&' + list.fields[scope[iterator + 'SearchField' + modifier]].searchField + '__';
                            } else if (list.fields[scope[iterator + 'SearchField' + modifier]].sourceModel) {
                                // handle fields whose source is a related model e.g. inventories.organization
                                scope[iterator + 'SearchParams'] += '&' + list.fields[scope[iterator + 'SearchField' + modifier]].sourceModel + '__' +
                                    list.fields[scope[iterator + 'SearchField' + modifier]].sourceField + '__';
                            } else if ( list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'select' &&
                                Empty(scope[iterator + 'SearchSelectValue' + modifier].value) ) {
                                scope[iterator + 'SearchParams'] += '&' + scope[iterator + 'SearchField' + modifier] + '__';
                            } else if ( list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'select' &&
                                !Empty(scope[iterator + 'SearchSelectValue' + modifier].value) ) {
                                scope[iterator + 'SearchParams'] += '&' + scope[iterator + 'SearchField' + modifier];
                            } else {
                                scope[iterator + 'SearchParams'] += '&' + scope[iterator + 'SearchField' + modifier] + '__';
                            }

                            if (list.fields[scope[iterator + 'SearchField' + modifier]].searchType &&
                                (list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'int' ||
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'boolean')) {
                                scope[iterator + 'SearchParams'] += 'int=';
                            } else if (list.fields[scope[iterator + 'SearchField' + modifier]].searchType &&
                                list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'gtzero') {
                                scope[iterator + 'SearchParams'] += 'gt=0';
                            } else if (list.fields[scope[iterator + 'SearchField' + modifier]].searchType &&
                                list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'isnull') {
                                scope[iterator + 'SearchParams'] += 'isnull=';
                            } else if ( (list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'select') &&
                                Empty(scope[iterator + 'SearchSelectValue' + modifier].value) && !/\_\_$/.test(scope[iterator + 'SearchParams']) ) {
                                scope[iterator + 'SearchParams'] += '=iexact=';
                            } else if (list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'in') {
                                if (!/\_\_$/.test(scope[iterator + 'SearchParams'])) {
                                    scope[iterator + 'SearchParams'] += '__';
                                }
                                scope[iterator + 'SearchParams'] += 'in=';
                            } else if (/\_\_$/.test(scope[iterator + 'SearchParams'])) {
                                scope[iterator + 'SearchParams'] += 'icontains=';
                            } else {
                                scope[iterator + 'SearchParams'] += scope[iterator + 'SearchType' + modifier] + '=';
                            }

                            if (list.fields[scope[iterator + 'SearchField' + modifier]].searchType &&
                                (list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'boolean' ||
                                    list.fields[scope[iterator + 'SearchField' + modifier]].searchType === 'select')) {
                                scope[iterator + 'SearchParams'] += scope[iterator + 'SearchSelectValue' + modifier].value;
                            } else {
                                if ((!list.fields[scope[iterator + 'SearchField' + modifier]].searchType) ||
                                    (list.fields[scope[iterator + 'SearchField' + modifier]].searchType &&
                                        list.fields[scope[iterator + 'SearchField' + modifier]].searchType !== 'or' &&
                                        list.fields[scope[iterator + 'SearchField' + modifier]].searchType !== 'gtzero')) {
                                    scope[iterator + 'SearchParams'] += encodeURI(scope[iterator + 'SearchValue' + modifier]);
                                }
                            }
                        }
                    }
                }

                if ((iterator === 'inventory' && scope.inventoryFailureFilter) ||
                    (iterator === 'host' && scope.hostFailureFilter)) {
                    //Things that bypass the search widget. Should go back and add a second widget possibly on
                    //inventory pages and eliminate this
                    scope[iterator + 'SearchParams'] += '&has_active_failures=true';
                }

                if (sort_order) {
                    scope[iterator + 'SearchParams'] += (scope[iterator + 'SearchParams']) ? '&' : '';
                    scope[iterator + 'SearchParams'] += 'order_by=' + encodeURI(sort_order);
                }
                e.stopPropagation();
                scope.$emit('doSearch', iterator, page, load, calcOnly, deferWaitStop);
            });

            scope.startSearch = function (e, iterator) {
                // If use clicks enter while on input field, start the search
                if (e.keyCode === 13) {
                    scope.search(iterator);
                }
            };

            /**
             * Initiate a searh.
             *
             *   @iterator:      required, list.iterator value
             *   @Page:          optional. Added to accomodate back function on Job Events detail.
             *   @Load:          optional, set to false if 'Loading' message not desired
             *   @calcOnly:      optional, set to true when you want to calc or figure out search params without executing the search
             *   @deferWaitStop: optional, when true refresh.js will NOT issue Wait('stop'), thus leaving the spinner. Caller is then
             *                             responsible for stopping the spinner post refresh.
             *   @spinner:       optional, if false, don't show the spinner.
             */
            scope.search = function (iterator, page, load, calcOnly, deferWaitStop, spinner) {
                page = page || null;
                load = (load || !scope[set] || scope[set].length === 0) ? true : false;
                calcOnly = (calcOnly) ? true : false;
                deferWaitStop = (deferWaitStop) ? true : false;
                spinner = (spinner === undefined) ? true : spinner;
                if (load) {
                    scope[set] = [];  //clear the list array to make sure 'Loading' is the only thing visible on the list
                }
                scope.$emit('prepareSearch', iterator, page, load, calcOnly, deferWaitStop, spinner);
            };


            scope.sort = function (iterator, fld) {
                // Reset sort icons back to 'icon-sort' on all columns
                // except the one clicked.
                $('.list-header').each(function () {
                    if ($(this).attr('id') !== iterator + '-' + fld + '-header') {
                        var icon = $(this).find('i');
                        icon.attr('class', 'fa fa-sort');
                    }
                });

                // Toggle the icon for the clicked column
                // and set the sort direction
                var icon = $('#' + iterator + '-' + fld + '-header i'),
                    direction = '';
                if (icon.hasClass('fa-sort')) {
                    icon.removeClass('fa-sort');
                    icon.addClass('fa-sort-up');
                } else if (icon.hasClass('fa-sort-up')) {
                    icon.removeClass('fa-sort-up');
                    icon.addClass('fa-sort-down');
                    direction = '-';
                } else if (icon.hasClass('fa-sort-down')) {
                    icon.removeClass('fa-sort-down');
                    icon.addClass('fa-sort-up');
                }

                // Set the sorder order value and call the API to refresh the list with the new order
                if (list.fields[fld].searchField) {
                    sort_order = direction + list.fields[fld].searchField;
                } else if (list.fields[fld].sortField) {
                    sort_order = direction + list.fields[fld].sortField;
                } else {
                    if (list.fields[fld].sourceModel) {
                        sort_order = direction + list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
                    } else {
                        sort_order = direction + fld;
                    }
                }

                scope[list.iterator + '_current_search_params'].sort_order = sort_order;
                Store(iterator + '_current_search_params', scope[iterator + '_current_search_params']);

                scope.search(list.iterator);
            };

            // Call after modal dialogs to remove any lingering callbacks
            scope.searchCleanup = function () {
                scope.removeDoSearch();
                scope.removePrepareSearch();
                scope.removePrepareSearch2();
            };

        };
    }
]);