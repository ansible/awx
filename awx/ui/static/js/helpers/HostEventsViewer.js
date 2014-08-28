/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HostEventsViewer.js
 *
 *  View a list of events for a given job and host
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:HostEventsViewer
 * @description   view a list of events for a given job and host
*/
'use strict';

angular.module('HostEventsViewerHelper', ['ModalDialog', 'Utilities', 'EventViewerHelper'])

    .factory('HostEventsViewer', ['$log', '$compile', 'CreateDialog', 'Wait', 'GetBasePath', 'Empty', 'GetEvents', 'EventViewer',
    function($log, $compile, CreateDialog, Wait, GetBasePath, Empty, GetEvents, EventViewer) {
        return function(params) {
            var parent_scope = params.scope,
                scope = parent_scope.$new(true),
                job_id = params.job_id,
                url = params.url,
                title = params.title, //optional
                fixHeight, buildTable,
                lastID, setStatus, buildRow, status;

            // initialize the status dropdown
            scope.host_events_status_options = [
                { value: "all", name: "All" },
                { value: "changed", name: "Changed" },
                { value: "failed", name: "Failed" },
                { value: "ok", name: "OK" },
                { value: "unreachable", name: "Unreachable" }
            ];
            scope.host_events_search_name = params.name;
            status = (params.status) ?  params.status : 'all';
            scope.host_events_status_options.every(function(opt, idx) {
                if (opt.value === status) {
                    scope.host_events_search_status = scope.host_events_status_options[idx];
                    return false;
                }
                return true;
            });
            if (!scope.host_events_search_status) {
                scope.host_events_search_status = scope.host_events_status_options[0];
            }

            $log.debug('job_id: ' + job_id + ' url: ' + url + ' title: ' + title + ' name: ' + name + ' status: ' + status);

            scope.eventsSearchActive = (scope.host_events_search_name) ? true : false;

            if (scope.removeModalReady) {
                scope.removeModalReady();
            }
            scope.removeModalReady = scope.$on('ModalReady', function() {
                scope.hostViewSearching = false;
                $('#host-events-modal-dialog').dialog('open');
            });

            if (scope.removeJobReady) {
                scope.removeJobReady();
            }
            scope.removeEventReady = scope.$on('EventsReady', function(e, data, maxID) {
                var elem, html;

                lastID = maxID;
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
                    onClose: function() {
                        try {
                            scope.$destroy();
                        }
                        catch(e) {
                            //ignore
                        }
                    },
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
                scope.hostViewSearching = false;
                elem = angular.element(document.getElementById('host-events'));
                $compile(elem)(scope);
            });

            setStatus = function(result) {
                var msg = '', status = 'ok', status_text = 'OK';
                if (!result.task && result.event_data && result.event_data.res && result.event_data.res.ansible_facts) {
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
                if (result.event_data.res && result.event_data.res.msg) {
                    msg = result.event_data.res.msg;
                }
                result.msg = msg;
                result.status = status;
                result.status_text = status_text;
                return result;
            };

            buildRow = function(res) {
                var html = '';
                html += "<tr>\n";
                html += "<td class=\"col-md-3\"><a href=\"\" ng-click=\"showDetails(" + res.id + ")\" aw-tool-tip=\"Click to view details\" data-placement=\"top\"><i class=\"fa icon-job-" + res.status + "\"></i> " + res.status_text + "</a></td>\n";
                html += "<td class=\"col-md=3\" ng-non-bindable>" + res.host_name + "</td>\n";
                html += "<td class=\"col-md-3\" ng-non-bindable>" + res.play + "</td>\n";
                html += "<td class=\"col-md-3\" ng-non-bindable>" + res.task + "</td>\n";
                html += "</tr>";
                return html;
            };

            buildTable = function(data) {
                var html = "<table class=\"table\">\n";
                html += "<tbody>\n";
                data.results.forEach(function(result) {
                    var res = setStatus(result);
                    html += buildRow(res);
                });
                html += "</tbody>\n";
                html += "</table>\n";
                return html;
            };

            fixHeight = function() {
                var available_height = $('#host-events-modal-dialog').height() - $('#host-events-modal-dialog #search-form').height() - $('#host-events-modal-dialog #fixed-table-header').height();
                $('#host-events').height(available_height);
                $log.debug('set height to: ' + available_height);
                // Check width and reset search fields
                if ($('#host-events-modal-dialog').width() <= 450) {
                    $('#host-events-modal-dialog #status-field').css({'margin-left': '7px'});
                }
                else {
                    $('#host-events-modal-dialog #status-field').css({'margin-left': '15px'});
                }
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

            scope.showDetails = function(id) {
                EventViewer({
                    scope: parent_scope,
                    url: GetBasePath('jobs') + job_id + '/job_events/?id=' + id,
                });
            };

            if (scope.removeEventsScrollDownBuild) {
                scope.removeEventsScrollDownBuild();
            }
            scope.removeEventsScrollDownBuild = scope.$on('EventScrollDownBuild', function(e, data, maxID) {
                var elem, html = '';
                lastID = maxID;
                data.results.forEach(function(result) {
                    var res = setStatus(result);
                    html += buildRow(res);
                });
                if (html) {
                    $('#host-events table tbody').append(html);
                    elem = angular.element(document.getElementById('host-events'));
                    $compile(elem)(scope);
                }
            });

            scope.hostEventsScrollDown = function() {
                GetEvents({
                    scope: scope,
                    url: url,
                    gt: lastID,
                    callback: 'EventScrollDownBuild'
                });
            };

        };
    }])

    .factory('GetEvents', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
        return function(params) {
            var url = params.url,
                scope = params.scope,
                gt = params.gt,
                callback = params.callback;

            if (scope.host_events_search_name) {
                url += '?host_name=' + scope.host_events_search_name;
            }
            else {
                url += '?host_name__isnull=false';
            }

            if (scope.host_events_search_status.value === 'changed') {
                url += '&event__icontains=runner&changed=true';
            }
            else if (scope.host_events_search_status.value === 'failed') {
                url += '&event__icontains=runner&failed=true';
            }
            else if (scope.host_events_search_status.value === 'ok') {
                url += '&event=runner_on_ok&changed=false';
            }
            else if (scope.host_events_search_status.value === 'unreachable') {
                url += '&event=runner_on_unreachable';
            }
            else if (scope.host_events_search_status.value === 'all') {
                url += '&event__icontains=runner&not__event=runner_on_skipped';
            }

            if (gt) {
                // used for endless scroll
                url += '&id__gt=' + gt;
            }

            url += '&page_size=50&order=id';

            scope.hostViewSearching = true;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    var lastID;
                    scope.hostViewSearching = false;
                    if (data.results.length > 0) {
                        lastID = data.results[data.results.length - 1].id;
                    }
                    scope.$emit(callback, data, lastID);
                })
                .error(function(data, status) {
                    scope.hostViewSearching = false;
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get events ' + url + '. GET returned: ' + status });
                });
        };
    }]);
