/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewer.js
 *
 */

'use strict';

angular.module('EventViewerHelper', ['ModalDialog', 'Utilities'])

    .factory('EventViewer', ['$compile', 'CreateDialog', 'GetEvent', 'Wait', 'AddTable', 'GetBasePath', 'LookUpName', 'Empty', 'AddPreFormattedText',
    function($compile, CreateDialog, GetEvent, Wait, AddTable, GetBasePath, LookUpName, Empty, AddPreFormattedText) {
        return function(params) {
            var parent_scope = params.scope,
                url = params.url,
                title = params.title, //optional
                scope = parent_scope.$new(true);

            if (scope.removeModalReady) {
                scope.removeModalReady();
            }
            scope.removeModalReady = scope.$on('ModalReady', function() {
                Wait('stop');
                $('#eventviewer-modal-dialog').dialog('open');
            });

            if (scope.removeJobReady) {
                scope.removeJobReady();
            }
            scope.removeEventReady = scope.$on('EventReady', function(e, data) {
                var elem;

                $('#status-form-container').empty();
                $('#stdout-form-container').empty();
                $('#stderr-form-container').empty();
                $('#traceback-form-container').empty();
                $('#eventview-tabs li:eq(1)').hide();
                $('#eventview-tabs li:eq(2)').hide();
                $('#eventview-tabs li:eq(3)').hide();

                AddTable({ scope: scope, id: 'status-form-container', event: data });

                if (data.stdout) {
                    $('#eventview-tabs li:eq(1)').show();
                    AddPreFormattedText({
                        id: 'stdout-form-container',
                        val: data.stdout
                    });
                }

                if (data.stderr) {
                    $('#eventview-tabs li:eq(2)').show();
                    AddPreFormattedText({
                        id: 'stderr-form-container',
                        val: data.stderr
                    });
                }

                if (data.traceback) {
                    $('#eventview-tabs li:eq(3)').show();
                    AddPreFormattedText({
                        id: 'traceback-form-container',
                        val: data.traceback
                    });
                }

                elem = angular.element(document.getElementById('eventviewer-modal-dialog'));
                $compile(elem)(scope);

                CreateDialog({
                    scope: scope,
                    width: 675,
                    height: 600,
                    minWidth: 450,
                    callback: 'ModalReady',
                    id: 'eventviewer-modal-dialog',
                    // onResizeStop: resizeText,
                    title: ( (title) ? title : 'Event Details' ),
                    onOpen: function() {
                        $('#eventview-tabs a:first').tab('show');
                        $('#dialog-ok-button').focus();
                    }
                });
            });

            GetEvent({
                url: url,
                scope: scope
            });

            scope.modalOK = function() {
                $('#eventviewer-modal-dialog').dialog('close');
                scope.$destroy();
            };
        };
    }])

    .factory('GetEvent', ['Wait', 'Rest', 'ProcessErrors', function(Wait, Rest, ProcessErrors) {
        return function(params) {
            var url = params.url,
                scope = params.scope;

            function getStatus(data) {
                return (data.results[0].event === "runner_on_unreachable") ? "unreachable" : (data.results[0].event === "runner_on_skipped") ? 'skipped' : (data.results[0].failed) ? 'failed' :
                            (data.results[0].changed) ? 'changed' : 'ok';
            }

            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    var key, event_data = {};
                    if (data.results.length > 0 && data.results[0].event_data.res) {
                        for (key in data.results[0].event_data) {
                            if (key !== "res") {
                                data.results[0].event_data.res[key] = data.results[0].event_data[key];
                            }
                        }
                        if (data.results[0].event_data.res.ansible_facts) {
                            // don't show fact gathering results
                            delete data.results[0].event_data.res.ansible_facts;
                        }
                        data.results[0].event_data.res.status = getStatus(data);
                        event_data = data.results[0].event_data.res;
                    }
                    else {
                        data.results[0].event_data.status = getStatus(data);
                        event_data = data.results[0].event_data;
                    }
                    // convert results to stdout
                    if (event_data.results && typeof event_data.results === "object" && Array.isArray(event_data.results)) {
                        event_data.stdout = "";
                        event_data.results.forEach(function(row) {
                            event_data.stdout += row + "\n";
                        });
                        delete event_data.results;
                    }
                    if (event_data.invocation) {
                        for (key in event_data.invocation) {
                            event_data[key] = event_data.invocation[key];
                        }
                        delete event_data.invocation;
                    }
                    event_data.parent = data.results[0].parent;
                    event_data.play = data.results[0].play;
                    event_data.task = data.results[0].task;
                    event_data.created = data.results[0].created;
                    event_data.role = data.results[0].role;
                    event_data.host_id = data.results[0].host;
                    event_data.host_name = data.results[0].host_name;
                    event_data.id = data.results[0].id;
                    event_data.parent = data.results[0].parent;
                    scope.$emit('EventReady', event_data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get event ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('LookUpName', ['Rest', 'ProcessErrors', 'Empty', function(Rest, ProcessErrors, Empty) {
        return function(params) {
            var url = params.url,
                scope_var = params.scope_var,
                scope = params.scope;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    if (scope_var === 'inventory_source') {
                        scope[scope_var + '_name'] = data.summary_fields.group.name;
                    }
                    else if (!Empty(data.name)) {
                        scope[scope_var + '_name'] = data.name;
                    }
                    if (!Empty(data.group)) {
                        // Used for inventory_source
                        scope.group = data.group;
                    }
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('AddTable', ['$compile', '$filter', 'Empty', function($compile, $filter, Empty) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                event = params.event,
                html = '', e;

            function keyToLabel(key) {
                var label = '';
                switch(key) {
                    case "id":
                        label = "Event ID";
                        break;
                    case "parent":
                        label = "Parent Event ID";
                        break;
                    case "rc":
                        label = "Return Code";
                        break;
                    default:
                        label = key.charAt(0).toUpperCase() + key.slice(1);
                        label = label.replace(/(\_.)/g, function(match) {
                                    var res;
                                    res = match.replace(/\_/,'');
                                    res = ' ' + res.toUpperCase();
                                    return res;
                                });
                }
                return label;
            }

            function parseJSON(obj) {
                var html = '', keys;
                if (typeof obj === "object") {
                    html += "<table class=\"table eventviewer-status\">\n";
                    html += "<tbody>\n";
                    keys = Object.keys(obj).sort();
                    keys.forEach(function(key) {
                        var label;
                        if (key !== "stdout" && key !== "stderr" && key !== "traceback" && key !== "host_id" && key !== "host") {
                            label = keyToLabel(key);
                            if (Empty(obj[key])) {
                                // exclude empty items
                            }
                            else if (typeof obj[key] === "boolean" || typeof obj[key] === "number" || typeof obj[key] === "string") {
                                html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">";
                                if (key === "status") {
                                    html += "<i class=\"fa icon-job-" + obj[key] + "\"></i> " + obj[key];
                                }
                                else if (key === "start" || key === "end" || key === "created") {
                                    html += $filter('date')(obj[key], 'MM/dd/yy HH:mm:ss');
                                }
                                else if (key === "host_name") {
                                    html += "<a href=\"#/home/hosts/?id=" + obj.host_id + "\" target=\"_blank\" " +
                                        "aw-tool-tip=\"Click to view host.<br />Opens in new tab or window.\" data-placement=\"right\" " +
                                        "ng-click=\"modalOK()\">" + obj[key] + "</a>";
                                }
                                else {
                                    html += obj[key];
                                }

                                html += "</td></tr>\n";
                            }
                            else if (typeof obj[key] === "object" && Array.isArray(obj[key])) {
                                html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">";
                                obj[key].forEach(function(row) {
                                    html += "[" + row + "],";
                                });
                                html = html.replace(/,$/,'');
                                html += "</td></tr>\n";
                            }
                            else if (typeof obj[key] === "object") {
                                html += "<tr><td class=\"key\">" + label + ":</td><td class=\"nested-table\">\n" + parseJSON(obj[key]) + "</td></tr>\n";
                            }
                        }
                    });
                    html += "</tbody>\n";
                    html += "</table>\n";
                }
                return html;
            }
            html = parseJSON(event);
            e = angular.element(document.getElementById(id));
            e.empty().html(html);
            $compile(e)(scope);
        };
    }])

    .factory('AddTextarea', [ function() {
        return function(params) {
            var container_id = params.container_id,
                val = params.val,
                fld_id = params.fld_id,
                html;
            html = "<div class=\"form-group\">\n" +
                "<textarea id=\"" + fld_id + "\" class=\"form-control mono-space\" rows=\"12\" readonly>" + val + "</textarea>" +
                "</div>\n";
            $('#' + container_id).empty().html(html);
        };
    }])

    .factory('AddPreFormattedText', [function() {
        return function(params) {
            var id = params.id,
                val = params.val,
                html;
            html = "<pre>" + val + "</pre>\n";
            $('#' + id).empty().html(html);
        };
    }]);