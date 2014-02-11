/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  SelectionHelper
 *  Used in list controllers where the list might also be used as a selection list.
 *
 *  SelectionInit( {
 *      scope: <list scope>,
 *      list: <list object>
 *      })
 */

'use strict';

angular.module('SelectionHelper', ['Utilities', 'RestServices'])

.factory('SelectionInit', ['Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 'Wait',
    function (Rest, Alert, ProcessErrors, ReturnToCaller, Wait) {
        return function (params) {

            var scope = params.scope,
                list = params.list,
                target_url = params.url,
                returnToCaller = params.returnToCaller,
                selected;

            if (params.selected !== undefined) {
                selected = params.selected;
            } else {
                selected = []; //array of selected row IDs
            }

            scope.formModalActionDisabled = true;
            scope.disableSelectBtn = true;

            // toggle row selection
            scope['toggle_' + list.iterator] = function (id, ischeckbox) {
                var i, j, found;
                for (i = 0; i < scope[list.name].length; i++) {
                    if (scope[list.name][i].id === id) {
                        if ((scope[list.name][i].checked === '0' && !ischeckbox) || (scope[list.name][i].checked === 1 && ischeckbox)) {
                            // select the row
                            scope[list.name][i].checked = '1';
                            scope[list.name][i].success_class = 'success';

                            // add selected object to the array
                            found = false;
                            for (j = 0; j < selected.length; j++) {
                                if (selected[j].id === id) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                selected.push(scope[list.name][i]);
                            }
                        } else {
                            // unselect the row
                            scope[list.name][i].checked = '0';
                            scope[list.name][i].success_class = '';

                            // remove selected object from the array
                            for (j = 0; j < selected.length; j++) {
                                if (selected[j].id === id) {
                                    selected.splice(j, 1);
                                    break;
                                }
                            }
                        }
                    }
                }
                if (selected.length > 0) {
                    scope.formModalActionDisabled = false;
                    scope.disableSelectBtn = false;
                } else {
                    scope.formModalActionDisabled = true;
                    scope.disableSelectBtn = true;
                }
            };

            // Add the selections
            scope.finishSelection = function () {
                Rest.setUrl(target_url);
                
                var queue = [], j;
                
                scope.formModalActionDisabled = true;
                scope.disableSelectBtn = true;

                Wait('start');

                function finished() {
                    selected = [];
                    if (returnToCaller !== undefined) {
                        ReturnToCaller(returnToCaller);
                    } else {
                        $('#form-modal').modal('hide');
                        scope.$emit('modalClosed');
                    }
                }

                function postIt(data) {
                    Rest.post(data)
                        .success(function (data, status) {
                            queue.push({ result: 'success', data: data, status: status });
                            scope.$emit('callFinished');
                        })
                        .error(function (data, status, headers) {
                            queue.push({ result: 'error', data: data, status: status, headers: headers });
                            scope.$emit('callFinished');
                        });
                }

                if (scope.callFinishedRemove) {
                    scope.callFinishedRemove();
                }
                scope.callFinishedRemove = scope.$on('callFinished', function () {
                    // We call the API for each selected item. We need to hang out until all the api
                    // calls are finished.
                    var i, errors=0;
                    if (queue.length === selected.length) {
                        Wait('stop');
                        for (i = 0; i < queue.length; i++) {
                            if (queue[i].result === 'error') {
                                ProcessErrors(scope, queue[i].data, queue[i].status, null, { hdr: 'POST Failure',
                                    msg: 'Failed to add ' + list.iterator + '. POST returned status: ' + queue[i].status });
                                errors++;
                            }
                        }
                        if (errors === 0) {
                            finished();
                        }
                    }
                });

                if (selected.length > 0) {
                    for (j = 0; j < selected.length; j++) {
                        postIt(selected[j]);
                    }
                } else {
                    finished();
                }
            };

            scope.formModalAction = scope.finishSelection;

            // Initialize our data set after a refresh (page change or search)
            if (scope.SelectPostRefreshRemove) {
                scope.SelectPostRefreshRemove();
            }
            scope.SelectPostRefreshRemove = scope.$on('PostRefresh', function () {
                var i, j, found;
                if (scope[list.name]) {
                    for (i = 0; i < scope[list.name].length; i++) {
                        found = false;
                        for (j = 0; j < selected.length; j++) {
                            if (selected[j].id === scope[list.name][i].id) {
                                found = true;
                                break;
                            }
                        }
                        if (found) {
                            scope[list.name][i].checked = '1';
                            scope[list.name][i].success_class = 'success';
                        } else {
                            scope[list.name][i].checked = '0';
                            scope[list.name][i].success_class = '';
                        }
                    }
                }
            });
        };
    }
]);