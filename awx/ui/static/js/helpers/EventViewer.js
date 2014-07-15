/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  EventsViewer.js
 *
 */

'use strict';

angular.module('EventViewerHelper', ['ModalDialog', 'Utilities', 'EventsViewerFormDefinition', 'HostsHelper'])

    .factory('EventViewer', ['$compile', 'CreateDialog', 'GetEvent', 'Wait', 'EventAddTable', 'GetBasePath', 'LookUpName', 'Empty', 'EventAddPreFormattedText',
    function($compile, CreateDialog, GetEvent, Wait, EventAddTable, GetBasePath, LookUpName, Empty, EventAddPreFormattedText) {
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
                $('#results-form-container').empty();
                $('#timing-form-container').empty();
                $('#stdout-form-container').empty();
                $('#stderr-form-container').empty();
                $('#traceback-form-container').empty();
                $('#eventview-tabs li:eq(1)').hide();
                $('#eventview-tabs li:eq(2)').hide();
                $('#eventview-tabs li:eq(3)').hide();
                $('#eventview-tabs li:eq(4)').hide();
                $('#eventview-tabs li:eq(5)').hide();

                EventAddTable({ scope: scope, id: 'status-form-container', event: data, section: 'Event' });

                if (EventAddTable({ scope: scope, id: 'results-form-container', event: data, section: 'Results'})) {
                    $('#eventview-tabs li:eq(1)').show();
                }

                if (EventAddTable({ scope: scope, id: 'timing-form-container', event: data, section: 'Timing' })) {
                    $('#eventview-tabs li:eq(2)').show();
                }

                if (data.stdout) {
                    $('#eventview-tabs li:eq(3)').show();
                    EventAddPreFormattedText({
                        id: 'stdout-form-container',
                        val: data.stdout
                    });
                }

                if (data.stderr) {
                    $('#eventview-tabs li:eq(4)').show();
                    EventAddPreFormattedText({
                        id: 'stderr-form-container',
                        val: data.stderr
                    });
                }

                if (data.traceback) {
                    $('#eventview-tabs li:eq(5)').show();
                    EventAddPreFormattedText({
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
                    onClose: function() {
                        try {
                            scope.$destroy();
                        }
                        catch(e) {
                            //ignore
                        }
                    },
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
                            data.results[0].event_data.res.task = "Gathering Facts";
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
                    event_data.play = data.results[0].play;
                    if (data.results[0].task) {
                        event_data.task = data.results[0].task;
                    }
                    event_data.created = data.results[0].created;
                    event_data.role = data.results[0].role;
                    event_data.host_id = data.results[0].host;
                    event_data.host_name = data.results[0].host_name;
                    if (event_data.host) {
                        delete event_data.host;
                    }
                    event_data.id = data.results[0].id;
                    event_data.parent = data.results[0].parent;
                    event_data.event = (data.results[0].event_display) ? data.results[0].event_display : data.results[0].event;
                    scope.$emit('EventReady', event_data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get event ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('EventAddTable', ['$compile', '$filter', 'Empty', 'EventsViewerForm', function($compile, $filter, Empty, EventsViewerForm) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                event = params.event,
                section = params.section,
                html = '', e;

            function parseJSON(obj) {
                var html = '', key, keys, found = false;
                if (typeof obj === "object") {
                    html += "<table class=\"table eventviewer-status\">\n";
                    html += "<tbody>\n";
                    keys = [];
                    for (key in EventsViewerForm.fields) {
                        if (EventsViewerForm.fields[key].section === section) {
                            keys.push(key);
                        }
                    }
                    keys.forEach(function(key) {
                        var label;
                        //if (EventsViewerForm.fields[key] && EventsViewerForm.fields[key].section === section) {
                        label = EventsViewerForm.fields[key].label;
                        if (Empty(obj[key])) {
                            // exclude empty items
                        }
                        else if (typeof obj[key] === "boolean" || typeof obj[key] === "number" || typeof obj[key] === "string") {
                            found = true;
                            html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">";
                            if (key === "status") {
                                html += "<i class=\"fa icon-job-" + obj[key] + "\"></i> " + obj[key];
                            }
                            else if (key === "start" || key === "end" || key === "created") {
                                if (!/Z$/.test(obj[key])) {
                                    //sec = parseInt(obj[key].substr(obj[key].length - 6, 6),10) / 1000);
                                    //obj[key] = obj[key].replace(/\d{6}$/,sec) + 'Z';
                                    obj[key] = obj[key].replace(/\ /,'T') + 'Z';
                                    html += $filter('date')(obj[key], 'MM/dd/yy HH:mm:ss.sss');
                                }
                                else {
                                    html += $filter('date')(obj[key], 'MM/dd/yy HH:mm:ss');
                                }
                            }
                            else if (key === "host_name" && obj.host_id) {
                                html += "<a href=\"/#/home/hosts/?id=" + obj.host_id + "\" target=\"_blank\" " +
                                    "aw-tool-tip=\"View host. Opens in new tab or window.\" data-placement=\"top\" " +
                                    ">" + obj[key] + "</a>";
                            }
                            else {
                                html += obj[key];
                            }

                            html += "</td></tr>\n";
                        }
                        else if (typeof obj[key] === "object" && Array.isArray(obj[key])) {
                            found = true;
                            html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">";
                            obj[key].forEach(function(row) {
                                html += "[" + row + "],";
                            });
                            html = html.replace(/,$/,'');
                            html += "</td></tr>\n";
                        }
                        else if (typeof obj[key] === "object") {
                            found = true;
                            html += "<tr><td class=\"key\">" + label + ":</td><td class=\"nested-table\">\n" + parseJSON(obj[key]) + "</td></tr>\n";
                        }
                        //}
                    });
                    html += "</tbody>\n";
                    html += "</table>\n";
                }
                return (found) ? html : '';
            }
            html = parseJSON(event);
            e = angular.element(document.getElementById(id));
            e.empty();
            if (html) {
                e.html(html);
                $compile(e)(scope);
            }
            return (html) ? true : false;
        };
    }])

    .factory('EventAddTextarea', [ function() {
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

    .factory('EventAddPreFormattedText', [function() {
        return function(params) {
            var id = params.id,
                val = params.val,
                html;
            html = "<pre>" + val + "</pre>\n";
            $('#' + id).empty().html(html);
        };
    }]);
