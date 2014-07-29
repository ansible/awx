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
                event_id = params.event_id,
                parent_id = params.parent_id,
                title = params.title, //optional
                scope = parent_scope.$new(true),
                current_event;

            if (scope.removeShowNextEvent) {
                scope.removeShowNextEvent();
            }
            scope.removeShowNextEvent = scope.$on('ShowNextEvent', function(e, data, show_event) {
                scope.events = data;
                $('#event-next-spinner').hide(400);
                if (show_event === 'prev') {
                    showEvent(scope.events.length - 1);
                }
                else if (show_event === 'next') {
                    showEvent(0);
                }
            });

            // show scope.events[idx]
            function showEvent(idx) {
                var show_tabs = false, elem, data;

                if (idx > scope.events.length - 1) {
                    GetEvent({
                        scope: scope,
                        url: scope.next_event_set,
                        show_event: 'next'
                    });
                    return;
                }

                if (idx < 0) {
                    GetEvent({
                        scope: scope,
                        url: scope.prev_event_set,
                        show_event: 'prev'
                    });
                    return;
                }

                data = scope.events[idx];
                current_event = idx;

                $('#status-form-container').empty();
                $('#results-form-container').empty();
                $('#timing-form-container').empty();
                $('#stdout-form-container').empty();
                $('#stderr-form-container').empty();
                $('#traceback-form-container').empty();
                $('#json-form-container').empty();
                $('#eventview-tabs li:eq(1)').hide();
                $('#eventview-tabs li:eq(2)').hide();
                $('#eventview-tabs li:eq(3)').hide();
                $('#eventview-tabs li:eq(4)').hide();
                $('#eventview-tabs li:eq(5)').hide();
                $('#eventview-tabs li:eq(6)').hide();

                EventAddTable({ scope: scope, id: 'status-form-container', event: data, section: 'Event' });

                if (EventAddTable({ scope: scope, id: 'results-form-container', event: data, section: 'Results'})) {
                    show_tabs = true;
                    $('#eventview-tabs li:eq(1)').show();
                }

                if (EventAddTable({ scope: scope, id: 'timing-form-container', event: data, section: 'Timing' })) {
                    show_tabs = true;
                    $('#eventview-tabs li:eq(2)').show();
                }

                if (data.stdout) {
                    show_tabs = true;
                    $('#eventview-tabs li:eq(3)').show();
                    EventAddPreFormattedText({
                        id: 'stdout-form-container',
                        val: data.stdout
                    });
                }

                if (data.stderr) {
                    show_tabs = true;
                    $('#eventview-tabs li:eq(4)').show();
                    EventAddPreFormattedText({
                        id: 'stderr-form-container',
                        val: data.stderr
                    });
                }

                if (data.traceback) {
                    show_tabs = true;
                    $('#eventview-tabs li:eq(5)').show();
                    EventAddPreFormattedText({
                        id: 'traceback-form-container',
                        val: data.traceback
                    });
                }

                show_tabs = true;
                $('#eventview-tabs li:eq(6)').show();
                EventAddPreFormattedText({
                    id: 'json-form-container',
                    val: JSON.stringify(data, null, 2)
                });

                if (!show_tabs) {
                    $('#eventview-tabs').hide();
                }

                elem = angular.element(document.getElementById('eventviewer-modal-dialog'));
                $compile(elem)(scope);
            }

            function setButtonMargin() {
                var width = ($('.ui-dialog[aria-describedby="eventviewer-modal-dialog"] .ui-dialog-buttonpane').innerWidth() / 2) - $('#events-next-button').outerWidth() - 73;
                $('#events-next-button').css({'margin-right': width + 'px'});
            }

            function addSpinner() {
                var position;
                if ($('#event-next-spinner').length > 0) {
                    $('#event-next-spinner').remove();
                }
                position = $('#events-next-button').position();
                $('#events-next-button').after('<i class="fa fa-cog fa-spin" id="event-next-spinner" style="display:none; position:absolute; top:' + (position.top + 15) + 'px; left:' + (position.left + 75) + 'px;"></i>');
            }

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
                var btns;
                scope.events = data;

                if (event_id) {
                    // find and show the selected event
                    data.every(function(row, idx) {
                        if (parseInt(row.id,10) === parseInt(event_id,10)) {
                            current_event = idx;
                            return false;
                        }
                        return true;
                    });
                }
                else {
                    current_event = 0;
                }
                showEvent(current_event);

                btns = [];
                if (scope.events.length > 1) {
                    btns.push({
                        label: "Prev",
                        onClick: function () {
                            if (current_event - 1 === 0 && !scope.prev_event_set) {
                                $('#events-prev-button').prop('disabled', true);
                            }
                            if (current_event - 1 < scope.events.length - 1) {
                                $('#events-next-button').prop('disabled', false);
                            }
                            showEvent(current_event - 1);
                        },
                        icon: "fa-chevron-left",
                        "class": "btn btn-primary",
                        id: "events-prev-button"
                    });
                    btns.push({
                        label: "Next",
                        onClick: function() {
                            if (current_event + 1 > 0) {
                                $('#events-prev-button').prop('disabled', false);
                            }
                            if (current_event + 1 >= scope.events.length - 1 && !scope.next_event_set) {
                                $('#events-next-button').prop('disabled', true);
                            }
                            showEvent(current_event + 1);
                        },
                        icon: "fa-chevron-right",
                        "class": "btn btn-primary",
                        id: "events-next-button"
                    });
                }
                btns.push({
                    label: "OK",
                    onClick: function() {
                        scope.modalOK();
                    },
                    icon: "",
                    "class": "btn btn-primary",
                    id: "dialog-ok-button"
                });

                CreateDialog({
                    scope: scope,
                    width: 675,
                    height: 600,
                    minWidth: 450,
                    callback: 'ModalReady',
                    id: 'eventviewer-modal-dialog',
                    // onResizeStop: resizeText,
                    title: ( (title) ? title : 'Event Details' ),
                    buttons: btns,
                    closeOnEscape: true,
                    onResizeStop: function() {
                        setButtonMargin();
                        addSpinner();
                    },
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
                        if (scope.events.length > 1 && current_event === 0 && !scope.prev_event_set) {
                            $('#events-prev-button').prop('disabled', true);
                        }
                        if ((current_event === scope.events.length - 1) && !scope.next_event_set) {
                            $('#events-next-button').prop('disabled', true);
                        }
                        if (scope.events.length > 1) {
                            setButtonMargin();
                            addSpinner();
                        }
                    }
                });
            });

            url += (/\/$/.test(url)) ? '?' : '&';
            url += (parent_id) ? 'parent=' + parent_id + '&page_size=50&order_by=id' : 'page_size=50&order_by=id';

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
                scope = params.scope,
                show_event = params.show_event,
                results= [];

            if (show_event) {
                $('#event-next-spinner').show();
            }
            else {
                Wait('start');
            }

            function getStatus(e) {
                return (e.event === "runner_on_unreachable") ? "unreachable" : (e.event === "runner_on_skipped") ? 'skipped' : (e.failed) ? 'failed' :
                            (e.changed) ? 'changed' : 'ok';
            }

            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.next_event_set = data.next;
                    scope.prev_event_set = data.previous;
                    data.results.forEach(function(event) {
                        var key, event_data = {};
                        if (event.event_data.res) {
                            for (key in event.event_data) {
                                if (key !== "res") {
                                    event.event_data.res[key] = event.event_data[key];
                                }
                            }
                            if (event.event_data.res.ansible_facts) {
                                // don't show fact gathering results
                                event.event_data.res.task = "Gathering Facts";
                                delete event.event_data.res.ansible_facts;
                            }
                            event.event_data.res.status = getStatus(event);
                            event_data = event.event_data.res;
                        }
                        else {
                            event.event_data.status = getStatus(event);
                            event_data = event.event_data;
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
                        event_data.play = event.play;
                        if (event.task) {
                            event_data.task = event.task;
                        }
                        event_data.created = event.created;
                        event_data.role = event.role;
                        event_data.host_id = event.host;
                        event_data.host_name = event.host_name;
                        if (event_data.host) {
                            delete event_data.host;
                        }
                        event_data.id = event.id;
                        event_data.parent = event.parent;
                        event_data.event = (event.event_display) ? event.event_display : event.event;
                        results.push(event_data);
                    });
                    if (show_event) {
                        scope.$emit('ShowNextEvent', results, show_event);
                    }
                    else {
                        scope.$emit('EventReady', results);
                    }
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

            function parseObject(obj) {
                // parse nested JSON objects. a mini version of parseJSON without references to the event form object.
                var i, key, html = '';
                for (key in obj) {
                    if (typeof obj[key] === "boolean" || typeof obj[key] === "number" || typeof obj[key] === "string") {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"value\">" + obj[key] + "</td></tr>";
                    }
                    else if (typeof obj[key] === "object" && Array.isArray(obj[key])) {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"value\">[";
                        for (i = 0; i < obj[key].length; i++) {
                            html += obj[key][i] + ",";
                        }
                        html = html.replace(/,$/,'');
                        html += "]</td></tr>\n";
                    }
                    else if (typeof obj[key] === "object") {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"nested-table\"><table>\n<tbody>\n" + parseObject(obj[key]) + "</tbody>\n</table>\n</td></tr>\n";
                    }
                }
                return html;
            }

            function parseItem(itm, key, label) {
                var i, html = '';
                if (Empty(itm)) {
                    // exclude empty items
                }
                else if (typeof itm === "boolean" || typeof itm === "number" || typeof itm === "string") {
                    html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">";
                    if (key === "status") {
                        html += "<i class=\"fa icon-job-" + itm + "\"></i> " + itm;
                    }
                    else if (key === "start" || key === "end" || key === "created") {
                        if (!/Z$/.test(itm)) {
                            itm = itm.replace(/\ /,'T') + 'Z';
                            html += $filter('date')(itm, 'MM/dd/yy HH:mm:ss.sss');
                        }
                        else {
                            html += $filter('date')(itm, 'MM/dd/yy HH:mm:ss');
                        }
                    }
                    else if (key === "host_name" && event.host_id) {
                        html += "<a href=\"/#/home/hosts/?id=" + event.host_id + "\" target=\"_blank\" " +
                            "aw-tool-tip=\"View host. Opens in new tab or window.\" data-placement=\"top\" " +
                            ">" + itm + "</a>";
                    }
                    else {
                        html += "<span ng-non-bindable>" + itm + "</span>";
                    }

                    html += "</td></tr>\n";
                }
                else if (typeof itm === "object" && Array.isArray(itm)) {
                    html += "<tr><td class=\"key\">" + label + ":</td><td class=\"value\">[";
                    for (i = 0; i < itm.length; i++) {
                        html += itm[i] + ",";
                    }
                    html = html.replace(/,$/,'');
                    html += "]</td></tr>\n";
                }
                else if (typeof itm === "object") {
                    html += "<tr><td class=\"key\">" + label + ":</td><td class=\"nested-table\"><table>\n<tbody>\n" + parseObject(itm) + "</tbody>\n</table>\n</td></tr>\n";
                }
                return html;
            }

            function parseJSON(obj) {
                var h, html = '', key, keys, found = false;
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
                        var h, label;
                        label = EventsViewerForm.fields[key].label;
                        h = parseItem(obj[key], key, label);
                        if (h) {
                            html += h;
                            found = true;
                        }
                    });
                    if (section === 'Results') {
                        // Add result fields that might be not be found the form object
                        // to results.
                        for (key in obj) {
                            h = '';
                            if (key !== 'host_id' && key !== 'parent' && key !== 'event' && key !== 'src' && key !== 'md5sum') {
                                if (!EventsViewerForm.fields[key]) {
                                    h = parseItem(obj[key], key, key);
                                    if (h) {
                                        html += h;
                                        found = true;
                                    }
                                }
                            }
                        }
                    }
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
                "<textarea ng-non-bindable id=\"" + fld_id + "\" class=\"form-control mono-space\" rows=\"12\" readonly>" + val + "</textarea>" +
                "</div>\n";
            $('#' + container_id).empty().html(html);
        };
    }])

    .factory('EventAddPreFormattedText', [function() {
        return function(params) {
            var id = params.id,
                val = params.val,
                html;
            html = "<pre ng-non-bindable>" + val + "</pre>\n";
            $('#' + id).empty().html(html);
        };
    }]);
