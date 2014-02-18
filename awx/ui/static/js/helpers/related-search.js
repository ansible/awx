/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  RelatedSearchHelper
 *
 *  All the parts for controlling the search widget on
 *  related collections.
 *
 *  SearchInit({
 *      scope: <scope>,
 *      relatedSets: <array of related collections {model_name, url, iterator}>,
 *      form: <form object used by FormGenerator>
 *      });
 *
 *
 */

'use strict';

angular.module('RelatedSearchHelper', ['RestServices', 'Utilities', 'RefreshRelatedHelper'])
    .factory('RelatedSearchInit', ['$timeout', 'Alert', 'Rest', 'RefreshRelated', 'Wait', 'Empty',
        function ($timeout, Alert, Rest, RefreshRelated, Wait, Empty) {
            return function (params) {

                var scope = params.scope,
                    relatedSets = params.relatedSets,
                    form = params.form, f;

                // Set default values
                function setDefaults(inIterator) {
                    var iterator, f, fld, set;
                    for (set in form.related) {
                        if (form.related[set].type !== 'tree' && (inIterator === undefined || inIterator === form.related[set].iterator)) {
                            iterator = form.related[set].iterator;
                            for (fld in form.related[set].fields) {
                                if (form.related[set].fields[fld].key) {
                                    scope[iterator + 'SearchField'] = fld;
                                    scope[iterator + 'SearchFieldLabel'] = form.related[set].fields[fld].label;
                                    break;
                                }
                            }
                            scope[iterator + 'SortOrder'] = null;
                            scope[iterator + 'SearchType'] = 'icontains';
                            scope[iterator + 'SearchTypeLabel'] = 'Contains';
                            scope[iterator + 'SearchValue'] = null;
                            scope[iterator + 'SelectShow'] = false;
                            //scope[iterator + 'HideSearchType'] = false;
                            scope[iterator + 'ShowStartBtn'] = true;
                            scope[iterator + 'HideAllStartBtn'] = false;

                            f = scope[iterator + 'SearchField'];
                            if (form.related[set].fields[f].searchType &&
                                    (form.related[set].fields[f].searchType === 'boolean' || form.related[set].fields[f].searchType === 'select')) {
                                scope[iterator + 'SelectShow'] = true;
                                scope[iterator + 'SearchSelectOpts'] = form.fields[f].searchOptions;
                            }
                            if (form.related[set].fields[f].searchType && form.related[set].fields[f].searchType === 'gtzero') {
                                scope[iterator + "InputHide"] = true;
                            }
                        }
                    }
                }

                setDefaults();

                scope.resetSearch = function (iterator) {
                    setDefaults(iterator);
                    scope.search(iterator);
                };

                // Functions to handle search widget changes
                scope.setSearchField = function (iterator, fld, label) {
                    
                    var f, related;

                    for (related in form.related) {
                        if (form.related[related].iterator === iterator) {
                            f = form.related[related].fields[fld];
                        }
                    }

                    scope[iterator + 'SearchFieldLabel'] = label;
                    scope[iterator + 'SearchField'] = fld;
                    scope[iterator + 'SearchValue'] = '';
                    scope[iterator + 'SelectShow'] = false;
                    //scope[iterator + 'HideSearchType'] = false;
                    scope[iterator + 'InputHide'] = false;
                    scope[iterator + 'ShowStartBtn'] = true;

                    if (f.searchType !== undefined && f.searchType === 'gtzero') {
                        scope[iterator + "InputHide"] = true;
                        scope[iterator + 'ShowStartBtn'] = false;
                    }
                    if (f.searchType !== undefined && (f.searchType === 'boolean' || f.searchType === 'select')) {
                        scope[iterator + 'SelectShow'] = true;
                        scope[iterator + 'SearchSelectOpts'] = f.searchOptions;
                    }

                    if (f.searchType !== undefined && f.searchType === 'int') {
                        //scope[iterator + 'HideSearchType'] = true;   
                        scope[iterator + 'SearchType'] = 'int';
                    }

                    scope.search(iterator);

                };

                scope.setSearchType = function (model, type, label) {
                    scope[model + 'SearchTypeLabel'] = label;
                    scope[model + 'SearchType'] = type;
                    scope.search(model);
                };

                scope.startSearch = function (e, iterator) {
                    // If use clicks enter while on input field, start the search
                    if (e.keyCode === 13) {
                        scope.search(iterator);
                    }
                };

                scope.search = function (iterator) {
                    //scope[iterator + 'SearchSpin'] = true;
                    Wait('start');
                    scope[iterator + 'Loading'] = true;
                    scope[iterator + 'HoldInput'] = true;

                    if (scope[iterator + 'SearchValue']) {
                        // User typed a value in input field
                        scope[iterator + 'ShowStartBtn'] = false;
                    }

                    if (iterator === 'host') {
                        if (scope.hostSearchField === 'has_active_failures') {
                            if (scope.hostSearchSelectValue && scope.hostSearchSelectValue.value === 1) {
                                scope.hostFailureFilter = true;
                            } else {
                                scope.hostFailureFilter = false;
                            }
                        }
                    }

                    var fld, key, set, url, sort_order;
                    for (key in relatedSets) {
                        if (relatedSets[key].iterator === iterator) {
                            set = key;
                            url = relatedSets[key].url;
                            for (fld in form.related[key].fields) {
                                if (form.related[key].fields[fld].key) {
                                    if (form.related[key].fields[fld].desc) {
                                        sort_order = '-' + fld;
                                    } else {
                                        sort_order = fld;
                                    }
                                }
                            }
                            break;
                        }
                    }

                    sort_order = (scope[iterator + 'SortOrder'] === null) ? sort_order : scope[iterator + 'SortOrder'];
                    f = form.related[set].fields[scope[iterator + 'SearchField']];
                    if ((scope[iterator + 'SelectShow'] === false && !Empty(scope[iterator + 'SearchValue'])) ||
                        (scope[iterator + 'SelectShow'] && scope[iterator + 'SearchSelectValue']) ||
                        (f.searchType && f.searchType === 'gtzero')) {
                        if (f.sourceModel) {
                            // handle fields whose source is a related model e.g. inventories.organization
                            scope[iterator + 'SearchParams'] = f.sourceModel + '__' + f.sourceField + '__';
                        } else if (f.searchField) {
                            scope[iterator + 'SearchParams'] = f.searchField + '__';
                        } else {
                            scope[iterator + 'SearchParams'] = scope[iterator + 'SearchField'] + '__';
                        }

                        if (f.searchType && (f.searchType === 'int' || f.searchType === 'boolean')) {
                            scope[iterator + 'SearchParams'] += 'int=';
                        } else if (f.searchType && f.searchType === 'gtzero') {
                            scope[iterator + 'SearchParams'] += 'gt=0';
                        } else {
                            scope[iterator + 'SearchParams'] += scope[iterator + 'SearchType'] + '=';
                        }

                        if (f.searchType && (f.searchType === 'boolean' || f.searchType === 'select')) {
                            scope[iterator + 'SearchParams'] += scope[iterator + 'SearchSelectValue'].value;
                        } else if (f.searchType === undefined || f.searchType === 'gtzero') {
                            scope[iterator + 'SearchParams'] += encodeURI(scope[iterator + 'SearchValue']);
                        }
                        scope[iterator + 'SearchParams'] += (sort_order) ? '&order_by=' + encodeURI(sort_order) : '';
                    } else {
                        scope[iterator + 'SearchParams'] = (sort_order) ? 'order_by=' + encodeURI(sort_order) : '';
                    }
                    scope[iterator + '_page'] = 1;
                    url += (url.match(/\/$/)) ? '?' : '&';
                    url += scope[iterator + 'SearchParams'];
                    url += (scope[iterator + '_page_size']) ? '&page_size=' + scope[iterator + '_page_size'] : "";
                    RefreshRelated({ scope: scope, set: set, iterator: iterator, url: url });
                };


                scope.sort = function (iterator, fld) {
                    var sort_order, icon, direction, set;

                    // reset sort icons back to 'icon-sort' on all columns
                    // except the one clicked
                    $('.' + iterator + ' .list-header').each(function () {
                        if ($(this).attr('id') !== iterator + '-' + fld + '-header') {
                            var icon = $(this).find('i');
                            icon.attr('class', 'fa fa-sort');
                        }
                    });

                    // Toggle the icon for the clicked column
                    // and set the sort direction  
                    icon = $('#' + iterator + '-' + fld + '-header i');
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
                    for (set in form.related) {
                        if (form.related[set].iterator === iterator) {
                            if (form.related[set].fields[fld].sourceModel) {
                                sort_order = direction + form.related[set].fields[fld].sourceModel + '__' +
                                    form.related[set].fields[fld].sourceField;
                            } else {
                                sort_order = direction + fld;
                            }
                        }
                    }
                    scope[iterator + 'SortOrder'] = sort_order;
                    scope.search(iterator);
                };
            };
        }
    ]);
