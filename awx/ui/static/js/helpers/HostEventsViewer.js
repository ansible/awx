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
                url = params.url,
                host_id = params.id,
                host_name = params.name,
                title = params.title, //optional
                scope = parent_scope.$new(true);

            $log.debug('host_id: ' + host_id + ' host_name: ' + host_name);

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

                //scope.host_events = data.results;
                //$log.debug(scope.host_events);

                scope.host_events = data.results;
                scope.host_events_search_name = host_name;
                scope.host_events_search_status = 'all';
                scope.host_events = [];
                html = "<table class=\"table\">\n";
                html += "<thead>\n";
                html += "<tr><th class=\"col-md-3\">Status</th>" +
                        "<th class=\"col-md-3\">Play</th>" +
                        "<th class=\"col-md-3\">Task</th>" +
                        "<th class=\"col-md-3\">Result</th></tr>\n";
                html += "</thead>\n";
                html += "<tbody>\n";
                data.results.forEach(function(result) {
                    var msg = '',
                        status = 'ok',
                        status_text = 'OK';
                    if (result.event_data.res) {
                        msg = result.event_data.res.msg;
                    }
                    if (result.event === "runner_on_no_hoss") {
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
                    html += "<td><i class=\"fa icon-job-" + status + "\"></i> <a href=\"\">" + status_text + "</a></td>\n";
                    html += "<td><a href=\"\">" + result.play + "</a></td>\n";
                    html += "<td><a href=\"\">" + result.task + "</a></td>\n";
                    html += "<td><a href=\"\">" + msg + "</a></td>";
                    html += "</tr>"
                });
                html += "</tbody>\n";
                html += "</table>\n";
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
                    // onResizeStop: resizeText,
                    title: ( (title) ? title : 'Host Events' )
                    //onOpen: function() {
                    //}
                });
            });

            GetEvents({
                url: url,
                scope: scope
            });

            scope.modalOK = function() {
                $('#host-events-modal-dialog').dialog('close');
                scope.$destroy();
            };
        };
    }])

    .factory('GetEvents', ['Wait', 'Rest', 'ProcessErrors', function(Wait, Rest, ProcessErrors) {
        return function(params) {
            var url = params.url,
                scope = params.scope;
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.$emit('EventsReady', data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get events ' + url + '. GET returned: ' + status });
                });
        };
    }]);
