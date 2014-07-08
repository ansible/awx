/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HostEventsViewer.js
 *
 *  View a list of events for a given job and host
 *
 */

'use strict';

angular.module('HostEventsViewerHelper', ['ModalDialog', 'Utilities'])

    .factory('HostEventsViewer', ['$log', '$compile', 'CreateDialog', 'Wait', 'GetBasePath', 'Empty', 'GetEvents',
    function($log, $compile, CreateDialog, Wait, GetBasePath, Empty, GetEvents) {
        return function(params) {
            var parent_scope = params.scope,
                scope = parent_scope.$new(true),
                url = params.url,
                title = params.title, //optional
                fixHeight, buildTable;

            scope.host_events_search_name = params.name;
            scope.host_events_search_status = 'all';

            scope.eventsSearchActive = (scope.host_events_search_name) ? true : false;

            if (scope.removeModalReady) {
                scope.removeModalReady();
            }
            scope.removeModalReady = scope.$on('ModalReady', function() {
                Wait('stop');
                $('#host-events-modal-dialog').dialog('open');
            });

            if (scope.removeJobReady) {
                scope.removeJobReady();
            }
            scope.removeEventReady = scope.$on('EventsReady', function(e, data) {
                var elem, html;

                html = buildTable(data);
                $('#host-events').html(html);
                elem = angular.element(document.getElementById('host-events-modal-dialog'));
                $compile(elem)(scope);

                CreateDialog({
                    scope: scope,
                    width: 675,
                    height: 600,
                    minWidth: 450,
                    callback: 'ModalReady',
                    id: 'host-events-modal-dialog',
                    onResizeStop: fixHeight,
                    title: ( (title) ? title : 'Host Events' ),
                    onOpen: function() {
                        fixHeight();
                    }
                });
            });

            if (scope.removeRefreshHTML) {
                scope.removeRefreshHTML();
            }
            scope.removeRefreshHTML = scope.$on('RefreshHTML', function(e, data) {
                var elem, html = buildTable(data);
                $('#host-events').html(html);
                elem = angular.element(document.getElementById('host-events'));
                $compile(elem)(scope);
                Wait('stop');
            });

            buildTable = function(data) {
                var html = "<table class=\"table\">\n";
                html += "<tbody>\n";
                data.results.forEach(function(result) {
                    var msg = '',
                        status = 'ok',
                        status_text = 'OK';

                    if (result.event_data.res && result.event_data.res.msg) {
                        msg = result.event_data.res.msg;
                    }
                    if (!result.task && result.event_data.res.ansible_facts) {
                        result.task = "Gathering Facts";
                    }
                    if (result.event === "runner_on_no_hosts") {
                        msg = "No hosts remaining";
                    }
                    if (result.event === 'runner_on_unreachable') {
                        status = 'unreachable';
                        status_text = 'Unreachable';
                    }
                    else if (result.failed) {
                        status = 'failed';
                        status_text = 'Failed';
                    }
                    else if (result.changed) {
                        status = 'changed';
                        status_text = 'Changed';
                    }
                    html += "<tr ng-click=\"showDetails()\" class=\"cursor-pointer\" aw-tool-tip=\"Click to view details\" data-placement=\"top\">\n";
                    html += "<td class=\"col-md-3\"><i class=\"fa icon-job-" + status + "\"></i> <a href=\"\">" + status_text + "</a></td>\n";
                    html += "<td class=\"col-md-3\"><a href=\"\">" + result.play + "</a></td>\n";
                    html += "<td class=\"col-md-3\"><a href=\"\">" + result.task + "</a></td>\n";
                    html += "<td class=\"col-md-3\"><a href=\"\">" + msg + "</a></td>";
                    html += "</tr>";
                });
                html += "</tbody>\n";
                html += "</table>\n";
                return html;
            };

            fixHeight = function() {
                var available_height = $('#host-events-modal-dialog').height() - $('#host-events-modal-dialog #search-form').height() - $('#host-events-modal-dialog #fixed-table-header').height();
                $('#host-events').height(available_height);
                $log.debug('set height to: ' + available_height);
            };

            GetEvents({
                url: url,
                scope: scope,
                callback: 'EventsReady'
            });

            scope.modalOK = function() {
                $('#host-events-modal-dialog').dialog('close');
                scope.$destroy();
            };

            scope.searchEvents = function() {
                scope.eventsSearchActive = (scope.host_events_search_name) ? true : false;
                GetEvents({
                    scope: scope,
                    url: url,
                    callback: 'RefreshHTML'
                });
            };

            scope.searchEventKeyPress = function(e) {
                if (e.keyCode === 13) {
                    scope.searchEvents();
                }
            };

        };
    }])

    .factory('GetEvents', ['Wait', 'Rest', 'ProcessErrors', function(Wait, Rest, ProcessErrors) {
        return function(params) {
            var url = params.url,
                scope = params.scope,
                callback = params.callback;

            if (scope.host_events_search_name) {
                url += '?host_name=' + scope.host_events_search_name;
            }
            else {
                url += '?host_name__isnull=false';
            }

            if (scope.host_events_search_status === 'changed') {
                url += '&event__icontains=runner&changed=true';
            }
            else if (scope.host_events_search_status === 'failed') {
                url += '&event__icontains=runner&failed=true';
            }
            else if (scope.host_events_search_status === 'ok') {
                url += '&event=runner_on_ok&changed=false';
            }
            else if (scope.host_events_search_status === 'unreachable') {
                url += '&event=runner_on_unreachable';
            }
            else if (!scope.host_events_search_status) {
                url += '&event__icontains=runner&not__event=runner_on_skipped';
            }

            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.$emit(callback, data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get events ' + url + '. GET returned: ' + status });
                });
        };
    }]);
