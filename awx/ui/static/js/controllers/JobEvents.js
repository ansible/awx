/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
/**
 * @ngdoc function
 * @name controllers.function:JobEvent
 * @description This controller's for the job event page
*/


export function JobEventsList($sce, $filter, $scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobEventList, GenerateList,
    LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, LookUpInit, ToggleChildren,
    FormatDate, EventView, Refresh, Wait) {

    ClearScope();

    var list = JobEventList,
        defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_events/', //?parent__isnull=1';
        generator = GenerateList,
        page;

    list.base = $location.path();
    $scope.job_id = $routeParams.id;
    $rootScope.flashMessage = null;
    $scope.selected = [];
    $scope.expand = true; //on load, automatically expand all nodes

    $scope.parentNode = 'parent-event'; // used in ngClass to dynamically set row level class and control
    $scope.childNode = 'child-event'; // link color and cursor

    if ($scope.removeSetHostLinks) {
        $scope.removeSetHostLinks();
    }
    $scope.removeSetHostLinks = $scope.$on('SetHostLinks', function (e, inventory_id) {
        for (var i = 0; i < $scope.jobevents.length; i++) {
            if ($scope.jobevents[i].summary_fields.host) {
                $scope.jobevents[i].hostLink = "/#/inventories/" + inventory_id;
                    //encodeURI($scope.jobevents[i].summary_fields.host.name);
            }
        }
    });

    function formatJSON(eventData) {
        //turn JSON event data into an html form

        var i, n, rows, fld, txt,
            html = '',
            found = false;

        if (eventData.res) {
            if (typeof eventData.res === 'string') {
                n = eventData.res.match(/\n/g);
                rows = (n) ? n.length : 1;
                rows = (rows > 10) ? 10 : rows;
                found = true;
                html += "<div class=\"form-group\">\n";
                html += "<label>Traceback:</label>\n";
                html += "<textarea readonly class=\"form-control nowrap\" rows=\"" + rows + "\">" + eventData.res + "</textarea>\n";
                html += "</div>\n";
            } else {
                for (fld in eventData.res) {
                    if ((fld === 'msg' || fld === 'stdout' || fld === 'stderr') &&
                        (eventData.res[fld] !== null && eventData.res[fld] !== '')) {
                        html += "<div class=\"form-group\">\n";
                        html += "<label>";
                        switch (fld) {
                        case 'msg':
                        case 'stdout':
                            html += 'Output:';
                            break;
                        case 'stderr':
                            html += 'Error:';
                            break;
                        }
                        html += "</label>\n";
                        n = eventData.res[fld].match(/\n/g);
                        rows = (n) ? n.length : 1;
                        rows = (rows > 10) ? 10 : rows;
                        html += "<textarea readonly class=\"form-control nowrap\" rows=\"" + rows + "\">" + eventData.res[fld] + "</textarea>\n";
                        //html += "<pre>" + eventData.res[fld] + "</pre>\n";
                        html += "</div>\n";
                        found = true;
                    }
                    if (fld === "results" && Array.isArray(eventData.res[fld]) && eventData.res[fld].length > 0) {
                        txt = '';
                        for (i = 0; i < eventData.res[fld].length; i++) {
                            txt += eventData.res[fld][i];
                        }
                        n = txt.match(/\n/g);
                        rows = (n) ? n.length : 1;
                        rows = (rows > 10) ? 10 : rows;
                        if (txt !== '') {
                            html += "<div class=\"form-group\">\n";
                            html += "<label>Results:</label>\n";
                            html += "<textarea readonly class=\"form-control nowrap mono-space\" rows=\"" + rows + "\">" + txt + "</textarea>\n";
                            //html += "<pre>" + txt + "</pre>\n";
                            html += "</div>\n";
                            found = true;
                        }
                    }
                    if (fld === "rc" && eventData.res[fld] !== '') {

                        html += "<div class=\"form-group\">\n";
                        html += "<label>Return Code:</label><div class=\"return-code\">" + eventData.res[fld] + "</div>\n";
                        //html += "<input type=\"text\" class=\"form-control nowrap mono-space\" value=\"" + eventData.res[fld] + "\" readonly >\n";
                        html += "</div>\n";
                        found = true;
                    }
                }
            }
            html = (found) ? "<form class=\"event-form\">\n" + html + "</form>\n" : '';
        }
        if (eventData.hosts) {
            html = "<span class=\"event-detail-host visible-sm\">" + eventData.host + "</span>\n" + html;
        } else {
            html = (html === '') ? null : html;
        }
        return html;
    }

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        // Initialize the parent levels

        generator.inject(list, { mode: 'edit', scope: $scope });

        var set = $scope[list.name], i;
        for (i = 0; i < set.length; i++) {
            set[i].event_display = set[i].event_display.replace(/^\u00a0*/g, '');
            if (set[i].event_level < 3) {
                set[i].ngicon = 'fa fa-minus-square-o node-toggle';
                set[i]['class'] = 'parentNode';
            } else {
                set[i].ngicon = 'fa fa-square-o node-no-toggle';
                set[i]['class'] = 'childNode';
                set[i].event_detail =  $sce.trustAsHtml(formatJSON(set[i].event_data));
            }
            set[i].show = true;
            set[i].spaces = set[i].event_level * 24;
            if ($scope.jobevents[i].failed) {
                $scope.jobevents[i].status = 'error';
                if (i === set.length - 1) {
                    $scope.jobevents[i].statusBadgeToolTip = "A failure occurred durring one or more playbook tasks.";
                } else if (set[i].event_level < 3) {
                    $scope.jobevents[i].statusBadgeToolTip = "A failure occurred within the children of this event.";
                } else {
                    $scope.jobevents[i].statusBadgeToolTip = "A failure occurred. Click to view details";
                }
            } else if ($scope.jobevents[i].changed) {
                $scope.jobevents[i].status = 'changed';
                if (i === set.length - 1) {
                    $scope.jobevents[i].statusBadgeToolTip = "A change was completed durring one or more playbook tasks.";
                } else if (set[i].event_level < 3) {
                    $scope.jobevents[i].statusBadgeToolTip = "A change was completed by one or more children of this event.";
                } else {
                    $scope.jobevents[i].statusBadgeToolTip = "A change was completed. Click to view details";
                }
            } else {
                $scope.jobevents[i].status = 'success';
                if (i === set.length - 1) {
                    $scope.jobevents[i].statusBadgeToolTip = "All playbook tasks completed successfully.";
                } else if (set[i].event_level < 3) {
                    $scope.jobevents[i].statusBadgeToolTip = "All the children of this event completed successfully.";
                } else {
                    $scope.jobevents[i].statusBadgeToolTip = "No errors occurred. Click to view details";
                }
            }
            //cDate = new Date(set[i].created);
            //set[i].created = FormatDate(cDate);
            set[i].created = $filter('longDate')(set[i].created);
        }

        // Need below lookup to get inventory_id, which is not on event record. Plus, good idea to get status and name
        // from job in the event that there are no job event records
        Rest.setUrl(GetBasePath('jobs') + $scope.job_id);
        Rest.get()
            .success(function (data) {
                $scope.job_status = data.status;
                $scope.job_name = data.summary_fields.job_template.name;
                LoadBreadCrumbs({
                    path: '/job_events/' + $scope.job_id,
                    title: $scope.job_id + ' - ' + data.summary_fields.job_template.name,
                    altPath: '/jobs'
                });
                $rootScope.breadcrumbs = [{
                    path: '/jobs',
                    title: $scope.job_id + ' - ' + data.summary_fields.job_template.name,
                }];
                $scope.$emit('SetHostLinks', data.inventory);
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to get job status for job: ' + $scope.job_id + '. GET status: ' + status
                });
            });
    });

    SearchInit({
        scope: $scope,
        set: 'jobevents',
        list: list,
        url: defaultUrl
    });

    page = ($routeParams.page) ? parseInt($routeParams.page,10) - 1 : null;

    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl,
        page: page
    });

    // Called from Inventories tab, host failed events link:
    if ($routeParams.host) {
        $scope[list.iterator + 'SearchField'] = 'host';
        $scope[list.iterator + 'SearchValue'] = $routeParams.host;
        $scope[list.iterator + 'SearchFieldLabel'] = list.fields.host.label;
    }

    $scope.search(list.iterator, $routeParams.page);

    $scope.toggle = function (id) {
        ToggleChildren({
            scope: $scope,
            list: list,
            id: id
        });
    };

    $scope.viewJobEvent = function (id) {
        EventView({
            event_id: id
        });
    };

    $scope.refresh = function () {
        $scope.jobSearchSpin = true;
        $scope.jobLoading = true;
        Wait('start');
        Refresh({
            scope: $scope,
            set: 'jobevents',
            iterator: 'jobevent',
            url: $scope.current_url
        });
    };
}

JobEventsList.$inject = ['$sce', '$filter', '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobEventList',
    'generateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'LookUpInit', 'ToggleChildren', 'FormatDate', 'EventView', 'Refresh', 'Wait'
];

export function JobEventsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, JobEventsForm, GenerateForm,
    Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath, FormatDate, EventView, Wait) {

    ClearScope();

    var form = JobEventsForm,
        generator = GenerateForm,
        defaultUrl = GetBasePath('base') + 'job_events/' + $routeParams.event_id + '/';

    generator.inject(form, { mode: 'edit', related: true, scope: $scope});
    generator.reset();

    // Retrieve detail record and prepopulate the form
    Wait('start');
    Rest.setUrl(defaultUrl);
    Rest.get()
        .success(function (data) {
            var cDate, fld, n, rows;
            $scope.event_display = data.event_display.replace(/^\u00a0*/g, '');
            LoadBreadCrumbs({ path: '/jobs/' + $routeParams.job_id + '/job_events/' + $routeParams.event_id, title: $scope.event_display });
            for (fld in form.fields) {
                switch (fld) {
                case 'status':
                    if (data.failed) {
                        $scope.status = 'error';
                    } else if (data.changed) {
                        $scope.status = 'changed';
                    } else {
                        $scope.status = 'success';
                    }
                    break;
                case 'created':
                    cDate = new Date(data.created);
                    $scope.created = FormatDate(cDate);
                    break;
                case 'host':
                    if (data.summary_fields && data.summary_fields.host) {
                        $scope.host = data.summary_fields.host.name;
                    }
                    break;
                case 'id':
                case 'task':
                case 'play':
                    $scope[fld] = data[fld];
                    break;
                case 'start':
                case 'end':
                    if (data.event_data && data.event_data.res && data.event_data.res[fld] !== undefined) {
                        cDate = new Date(data.event_data.res[fld]);
                        $scope[fld] = FormatDate(cDate);
                    }
                    break;
                case 'msg':
                case 'stdout':
                case 'stderr':
                case 'delta':
                case 'rc':
                    if (data.event_data && data.event_data.res && data.event_data.res[fld] !== undefined) {
                        $scope[fld] = data.event_data.res[fld];
                        if (form.fields[fld].type === 'textarea') {
                            n = data.event_data.res[fld].match(/\n/g);
                            rows = (n) ? n.length : 1;
                            rows = (rows > 15) ? 5 : rows;
                            $('textarea[name="' + fld + '"]').attr('rows', rows);
                        }
                    }
                    break;
                case 'module_name':
                case 'module_args':
                    if (data.event_data.res && data.event_data.res.invocation) {
                        $scope[fld] = data.event_data.res.invocation.fld;
                    }
                    break;
                }
            }
            Wait('stop');
        })
        .error(function (data) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve host: ' + $routeParams.event_id +
                '. GET status: ' + status });
        });

    $scope.navigateBack = function () {
        var url = '/jobs/' + $routeParams.job_id + '/job_events';
        if ($routeParams.page) {
            url += '?page=' + $routeParams.page;
        }
        $location.url(url);
    };

    $scope.rawView = function () {
        EventView({
            "event_id": $scope.id
        });
    };

}

JobEventsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobEventsForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'FormatDate', 'EventView', 'Wait'
];
