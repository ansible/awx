/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LookupHelper
 *  Build a lookup dialog
 *
 *  LookUpInit( {
 *      scope: <form scope>,
 *      form: <form object>,
 *      current_item: <id of item to select on open>,
 *      list: <list object>,
 *      field: <name of the form field with which the lookup is associated>,
 *      hdr: <optional. modal dialog header>
 *      })
 */

'use strict';

angular.module('LookUpHelper', ['RestServices', 'Utilities', 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'ApiLoader'])
    .factory('LookUpInit', ['Alert', 'Rest', 'GenerateList', 'SearchInit', 'PaginateInit', 'GetBasePath', 'FormatDate', 'Empty',
        function (Alert, Rest, GenerateList, SearchInit, PaginateInit, GetBasePath, FormatDate, Empty) {
            return function (params) {

                var scope = params.scope,
                    form = params.form,
                    list = params.list,
                    field = params.field,
                    postAction = params.postAction,
                    defaultUrl, name, hdr, watchUrl;

                if (params.url) {
                    // pass in a url value to override the default
                    defaultUrl = params.url;
                } else {
                    defaultUrl = (list.name === 'inventories') ? GetBasePath('inventory') : GetBasePath(list.name);
                }

                // Show pop-up 
                name = list.iterator.charAt(0).toUpperCase() + list.iterator.substring(1);
                hdr = (params.hdr) ? params.hdr : 'Select ' + name;

                watchUrl = (/\/$/.test(defaultUrl)) ? defaultUrl + '?' : defaultUrl + '&';
                watchUrl += form.fields[field].sourceField + '__' + 'iexact=:value';

                $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-url', watchUrl);
                $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-source', field);

                scope['lookUp' + name] = function () {

                    var master = {}, listGenerator, listScope;

                    // Generating the search list potentially kills the values held in scope for the field.
                    // We'll keep a copy in master{} that we can revert back to on cancel;
                    master[field] = scope[field];
                    master[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                        scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField];

                    listGenerator = GenerateList;
                    listScope = listGenerator.inject(list, { mode: 'lookup', hdr: hdr });

                    $('#lookup-modal').on('hidden.bs.modal', function () {
                        // Restore search settings
                        if (listScope.searchCleanup) {
                            listScope.searchCleanup();
                        }
                        // If user clicks cancel without making a selection, restore original values 
                        if (Empty(scope[field])) {
                            scope[field] = master[field];
                            scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                               master[form.fields[field].sourceModel + '_' + form.fields[field].sourceField];
                        }
                    });

                    listScope.selectAction = function () {

                        var i, found = false;
                        for (i = 0; i < listScope[list.name].length; i++) {
                            if (listScope[list.name][i].checked === '1') {
                                found = true;
                                scope[field] = listScope[list.name][i].id;
                                if (scope[form.name + '_form'] && form.fields[field] && form.fields[field].sourceModel) {
                                    scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                                        listScope[list.name][i][form.fields[field].sourceField];
                                    if (scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                                        scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]
                                            .$setValidity('awlookup', true);
                                    }
                                }
                                if (scope[form.name + '_form']) {
                                    scope[form.name + '_form'].$setDirty();
                                }
                                listGenerator.hide();
                            }
                        }
                        if (found === false) {
                            Alert('Missing Selection', 'Oops, you failed to make a selection. Click on a row to make your selection, ' +
                                'and then click the Select button.');
                        } else {
                            if (postAction) {
                                postAction();
                            }
                        }
                    };

                    listScope['toggle_' + list.iterator] = function (id) {
                        var i;
                        for (i = 0; i < scope[list.name].length; i++) {
                            if (listScope[list.name][i].id === id) {
                                listScope[list.name][i].checked = '1';
                                listScope[list.name][i].success_class = 'success';
                            } else {
                                listScope[list.name][i].checked = '0';
                                listScope[list.name][i].success_class = '';
                            }
                        }
                    };

                    SearchInit({
                        scope: listScope,
                        set: list.name,
                        list: list,
                        url: defaultUrl
                    });
                    PaginateInit({
                        scope: listScope,
                        list: list,
                        url: defaultUrl,
                        mode: 'lookup'
                    });

                    // If user made a selection previously, mark it as selected when modal loads 
                    if (listScope.lookupPostRefreshRemove) {
                        listScope.lookupPostRefreshRemove();
                    }
                    listScope.lookupPostRefreshRemove = scope.$on('PostRefresh', function () {
                        var fld, i;
                        for (fld in list.fields) {

                            if (list.fields[fld].type && list.fields[fld].type === 'date') {
                                //convert dates to our standard format
                                for (i = 0; i < scope[list.name].length; i++) {
                                    scope[list.name][i][fld] = FormatDate(new Date(scope[list.name][i][fld]));
                                }
                            }
                        }

                        // List generator creates the form, resetting it and losing the previously selected value. 
                        // If it's in the current set, find it and marke it as selected.
                        if (scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] !== '' &&
                            scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] !== null) {
                            for (i = 0; i < listScope[list.name].length; i++) {
                                if (listScope[list.name][i][form.fields[field].sourceField] ===
                                    scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                                    scope[field] = listScope[list.name][i].id;
                                    break;
                                }
                            }

                        }

                        if (!Empty(scope[field])) {
                            listScope['toggle_' + list.iterator](scope[field]);
                        }

                    });

                    listScope.search(list.iterator);

                };
            };
        }
    ]);
