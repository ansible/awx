/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LookupHelper
 *  Build a lookup dialog
 */

   /**
 * @ngdoc function
 * @name helpers.function:Lookup
 * @description
 *  LookUpInit( {
 *      scope: <caller's scope>,
 *      form: <form object>,
 *      current_item: <id of item to select on open>,
 *      list: <list object>,
 *      field: <name of the form field with which the lookup is associated>,
 *      hdr: <optional. modal dialog header>
 *      postAction: optional function to run after selection made,
 *      callback: optional label to $emit() on parent scope
 *      input_type: optional string that specifies whether lookup should have checkboxes or radio buttons. defaults to 'checkbox' --- added by JT 8/21/14
 *  })
 */

import listGenerator from 'tower/shared/list-generator/main';

export default
    angular.module('LookUpHelper', ['RestServices', 'Utilities', 'SearchHelper', 'PaginationHelpers', listGenerator.name, 'ApiLoader', 'ModalDialog'])

        .factory('LookUpInit', ['Alert', 'Rest', 'ProcessErrors', 'generateList', 'SearchInit', 'PaginateInit', 'GetBasePath', 'FormatDate', 'Empty', 'CreateDialog',
        function (Alert, Rest, ProcessErrors, GenerateList, SearchInit, PaginateInit, GetBasePath, FormatDate, Empty, CreateDialog) {
            return function (params) {

                var parent_scope = params.scope,
                    form = params.form,
                    list = params.list,
                    field = params.field,
                    instructions = params.instructions,
                    postAction = params.postAction,
                    callback = params.callback,
                    input_type = (params.input_type) ? params.input_type: "checkbox",
                    defaultUrl, name, watchUrl;

                if (params.url) {
                    // pass in a url value to override the default
                    defaultUrl = params.url;
                } else {
                    defaultUrl = (list.name === 'inventories') ? GetBasePath('inventory') : GetBasePath(list.name);
                }

                if ($('#htmlTemplate #lookup-modal-dialog').length > 0) {
                    $('#htmlTemplate #lookup-modal-dialog').empty();
                }
                else {
                    $('#htmlTemplate').append("<div id=\"lookup-modal-dialog\"></div>");
                }

                name = list.iterator.charAt(0).toUpperCase() + list.iterator.substring(1);

                watchUrl = (/\/$/.test(defaultUrl)) ? defaultUrl + '?' : defaultUrl + '&';
                watchUrl += form.fields[field].sourceField + '__' + 'iexact=:value';

                $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-url', watchUrl);
                $('input[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').attr('data-source', field);

                // Auto populate the field if there is only one result
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function (data) {
                         if (data.count === 1) {
                             parent_scope[field] = data.results[0].id;
                             if (parent_scope[form.name + '_form'] && form.fields[field] && form.fields[field].sourceModel) {
                                 parent_scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                                    data.results[0][form.fields[field].sourceField];
                                 if (parent_scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                                     parent_scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]
                                         .$setValidity('awlookup', true);
                                 }
                             }
                             if (parent_scope[form.name + '_form']) {
                                 parent_scope[form.name + '_form'].$setDirty();
                             }
                         }
                    })
                    .error(function (data, status) {
                        ProcessErrors(parent_scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to launch adhoc command. POST returned status: ' +
                                status });
                    });


                parent_scope['lookUp' + name] = function () {

                    var master = {},
                        scope = parent_scope.$new(),
                        name, hdr, buttons;

                    // Generating the search list potentially kills the values held in scope for the field.
                    // We'll keep a copy in master{} that we can revert back to on cancel;
                    master[field] = scope[field];
                    master[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                        scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField];

                    GenerateList.inject(list, {
                        mode: 'lookup',
                        id: 'lookup-modal-dialog',
                        scope: scope,
                        instructions: instructions,
                        input_type: input_type
                    });

                    name = list.iterator.charAt(0).toUpperCase() + list.iterator.substring(1);
                    hdr = (params.hdr) ? params.hdr : 'Select ' + name;

                    // Show pop-up
                    buttons = [{
                        label: "Cancel",
                        icon: "fa-times",
                        "class": "btn btn-default",
                        "id": "lookup-cancel-button",
                        onClick: function() {
                            $('#lookup-modal-dialog').dialog('close');
                        }
                    },{
                        label: "Select",
                        onClick: function() {
                            scope.selectAction();
                        },
                        icon: "fa-check",
                        "class": "btn btn-primary",
                        "id": "lookup-save-button"
                    }];

                    if (scope.removeModalReady) {
                        scope.removeModalReady();
                    }
                    scope.removeModalReady = scope.$on('ModalReady', function() {
                        $('#lookup-save-button').attr('disabled','disabled');
                        $('#lookup-modal-dialog').dialog('open');
                    });

                    CreateDialog({
                        scope: scope,
                        buttons: buttons,
                        width: 600,
                        height: (instructions) ? 625 : 500,
                        minWidth: 500,
                        title: hdr,
                        id: 'lookup-modal-dialog',
                        onClose: function() {
                            setTimeout( function() {
                                scope.$apply( function() {
                                    if (Empty(scope[field])) {
                                        scope[field] = master[field];
                                        scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                                        master[form.fields[field].sourceModel + '_' + form.fields[field].sourceField];
                                    }
                                });
                            }, 300);
                        },
                        callback: 'ModalReady'
                    });

                    SearchInit({
                        scope: scope,
                        set: list.name,
                        list: list,
                        url: defaultUrl
                    });

                    PaginateInit({
                        scope: scope,
                        list: list,
                        url: defaultUrl,
                        mode: 'lookup'
                    });

                    if (scope.lookupPostRefreshRemove) {
                        scope.lookupPostRefreshRemove();
                    }
                    scope.lookupPostRefreshRemove = scope.$on('PostRefresh', function () {
                        var fld, i;
                        for (fld in list.fields) {
                            if (list.fields[fld].type && list.fields[fld].type === 'date') {
                                //convert dates to our standard format
                                for (i = 0; i < scope[list.name].length; i++) {
                                    scope[list.name][i][fld] = FormatDate(new Date(scope[list.name][i][fld]));
                                }
                            }
                        }

                        // List generator creates the list, resetting it and losing the previously selected value.
                        // If the selected value is in the current set, find it and mark selected.
                        if (!Empty(parent_scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField])) {
                            scope[list.name].forEach(function(elem) {
                                if (elem[form.fields[field].sourceField] ===
                                    parent_scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                                    scope[field] = elem.id;
                                }
                            });

                        }

                        if (!Empty(scope[field])) {
                            scope['toggle_' + list.iterator](scope[field]);
                        }

                    });

                    scope.search(list.iterator);

                    scope.selectAction = function () {
                        var i, found = false;
                        for (i = 0; i < scope[list.name].length; i++) {
                            if (scope[list.name][i].checked === '1' || scope[list.name][i].checked===1) {
                                found = true;
                                parent_scope[field] = scope[list.name][i].id;
                                if (parent_scope[form.name + '_form'] && form.fields[field] && form.fields[field].sourceModel) {
                                    parent_scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField] =
                                        scope[list.name][i][form.fields[field].sourceField];
                                    if (parent_scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]) {
                                        parent_scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField]
                                            .$setValidity('awlookup', true);
                                    }
                                }
                                if (parent_scope[form.name + '_form']) {
                                    parent_scope[form.name + '_form'].$setDirty();
                                }
                            }
                        }
                        if (found) {
                            // Selection made
                            $('#lookup-modal-dialog').dialog('close');
                            if (postAction) {
                                postAction();
                            }
                            if (callback) {
                                parent_scope.$emit(callback);
                            }
                        }
                    };


                    scope['toggle_' + list.iterator] = function (id) {
                        var count = 0;
                        scope[list.name].forEach( function(row, i) {
                            if (row.id === id) {
                                if (row.checked === '0') {
                                    scope[list.name][i].checked = '1';
                                    scope[list.name][i].success_class = 'success';
                                }
                                else {
                                    scope[list.name][i].checked = '0';
                                    scope[list.name][i].success_class = '';
                                }
                            } else {
                                scope[list.name][i].checked = '0';
                                scope[list.name][i].success_class = '';
                            }
                        });
                        // Check if any rows are checked
                        scope[list.name].forEach(function(row) {
                            if (row.checked === '1') {
                                count++;
                            }
                        });
                        if (count === 0) {
                            $('#lookup-save-button').attr('disabled','disabled');
                        }
                        else {
                            $('#lookup-save-button').removeAttr('disabled');
                        }
                    };
                };
            };
        }]);
