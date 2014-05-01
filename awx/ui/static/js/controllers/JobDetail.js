/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 */

/* global _ */

'use strict';

function JobDetailController ($scope, $compile, $routeParams, ClearScope, Breadcrumbs, LoadBreadCrumbs, GetBasePath, Wait, Rest, ProcessErrors, DigestEvents,
    SelectPlay, SelectTask, Socket, GetElapsed, SelectHost) {

    ClearScope();

    var job_id = $routeParams.id,
        event_socket, job,
        event_queue = [],
        processed_events = [],
        scope = $scope,
        api_complete = false;
    
    scope.plays = [];
    scope.tasks = [];
    scope.hosts = [];
    scope.hostResults = [];
    scope.job_status = {};
    scope.job_id = job_id;
    scope.auto_scroll = false;
    scope.searchTaskHostsEnabled = true;
    scope.searchSummaryHostsEnabled = true;
    
    event_socket =  Socket({
        scope: scope,
        endpoint: "job_events"
    });
    
    event_socket.init();

    // Evaluate elements of an array, returning the set of elements that 
    // match a condition as expressed in a function
    //
    //    matches = myarray.find(function(x) { return x.id === 5 }); 
    //
    Array.prototype.find = function(parameterFunction) {
        var results = [];
        this.forEach(function(row) {
            if (parameterFunction(row)) {
                results.push(row);
            }
        });
        return results;
    };

    // Reduce an array of objects down to just the bits we want from each object by
    // passing in a function that returns just those parts.
    // 
    // new_array = myarray.reduce(function(x) { return { blah: x.blah, foo: x.foo } });
    //
    Array.prototype.reduce = function(parameterFunction) {
        var results= [];
        this.forEach(function(row) {
            results.push(parameterFunction(row));
        });
        return results;
    };


    // Apply each event to the view
    if (scope.removeEventsReady) {
        scope.removeEventsReady();
    }
    scope.removeEventsReady = scope.$on('EventsReady', function(e, events) {
        DigestEvents({
            scope: scope,
            events: events
        });
    });
    
    event_socket.on("job_events-" + job_id, function(data) {
        var matches;
        data.event = data.event_name;
        if (api_complete) {
            matches = processed_events.find(function(x) { return x === data.id; });
            if (matches.length === 0) {
                // event not processed
                scope.$emit('EventsReady', [ data ]);
            }
        }
        else {
            event_queue.push(data);
        }
    });


    if (scope.removeAPIComplete) {
        scope.removeAPIComplete();
    }
    scope.removeAPIComplete = scope.$on('APIComplete', function() {
        var events;
        if (event_queue.length > 0) {
            // Events arrived while we were processing API results
            events = event_queue.find(function(event) {
                var matched = false;
                processed_events.every(function(event_id) {
                    if (event_id === event.id) {
                        matched = true;
                        return false;
                    }
                    return true;
                });
                return (!matched);  //return true when event.id not in the list of processed_events
            });
            if (events.length > 0) {
                scope.$emit('EventsReady', events);
                api_complete = true;
            }
        }
        else {
            api_complete = true;
        }
    });

    // Get events, 50 at a time. When done, emit APIComplete
    if (scope.removeJobReady) {
        scope.removeJobReady();
    }
    scope.removeJobReady = scope.$on('JobReady', function(e, next) {
        Rest.setUrl(next);
        Rest.get()
            .success(function(data) {
                processed_events = processed_events.concat( data.results.reduce(function(x) { return x.id; }) );
                scope.$emit('EventsReady', data.results);
                if (data.next) {
                    scope.$emit('JobReady', data.next);
                }
                else {
                    Wait('stop');
                    scope.$emit('APIComplete');
                }
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve job events: ' + next + ' GET returned: ' + status });
            });
    });

    if (scope.removeGetCredentialNames) {
        scope.removeGetCredentialNames();
    }
    scope.removeGetCredentialNames = scope.$on('GetCredentialNames', function(e, data) {
        var url;
        if (data.credential) {
            url = GetBasePath('credentials') + data.credential + '/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.credential_name = data.name;
                })
                .error( function(data, status) {
                    scope.credential_name = '';
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        if (data.cloud_credential) {
            url = GetBasePath('credentials') + data.credential + '/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.cloud_credential_name = data.name;
                })
                .error( function(data, status) {
                    scope.credential_name = '';
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
    });
    
    Wait('start');
    
    // Load the job record
    Rest.setUrl(GetBasePath('jobs') + job_id + '/');
    Rest.get()
        .success(function(data) {
            job = data;
            scope.job_template_name = data.name;
            scope.project_name = (data.summary_fields.project) ? data.summary_fields.project.name : '';
            scope.inventory_name = (data.summary_fields.inventory) ? data.summary_fields.inventory.name : '';
            scope.job_template_url = '/#/job_templates/' + data.unified_job_template;
            scope.inventory_url = (scope.inventory_name && data.inventory) ? '/#/inventories/' + data.inventory : '';
            scope.project_url = (scope.project_name && data.project) ? '/#/projects/' + data.project : '';
            scope.job_type = data.job_type;
            scope.playbook = data.playbook;
            scope.credential = data.credential;
            scope.cloud_credential = data.cloud_credential;
            scope.forks = data.forks;
            scope.limit = data.limit;
            scope.verbosity = data.verbosity;
            scope.job_tags = data.job_tags;

            // In the case that the job is already completed, or an error already happened,
            // populate scope.job_status info
            scope.job_status.status = data.status;
            scope.job_status.started = data.started;
            scope.job_status.status_class = ((data.status === 'error' || data.status === 'failed') && data.job_explanation) ? "alert alert-danger" : "";
            scope.job_status.finished = data.finished;
            scope.job_status.explanation = data.job_explanation;
            if (data.started && data.finished) {
                scope.job_status.elapsed = GetElapsed({
                    start: data.started,
                    end: data.finished
                });
            }
            else {
                scope.job_status.elapsed = '00:00:00';
            }

            scope.$emit('JobReady', data.related.job_events + '?page_size=50&order_by=id');
            scope.$emit('GetCredentialNames', data);
        })
        .error(function(data, status) {
            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET returned: ' + status });
        });

    scope.selectPlay = function(id) {
        SelectPlay({
            scope: scope,
            id: id
        });
    };

    scope.selectTask = function(id) {
        SelectTask({
            scope: scope,
            id: id
        });
    };

    $("#hosts-slider-vertical").slider({
        orientation: "vertical",
        range: "min",
        min: 0,
        max: 100,
        value: 60,
        slide: function( event, ui ) {
            $( "#amount" ).val( ui.value );
        }
    });

    // Use debounce from the underscore library. We're including underscore
    // for the timezone stuff, so might as well take advantage of it.
    function adjustSize() {
        var height, ww = $(window).width();
        if (ww < 1240) {
            $('#job-summary-container').hide();
            $('#job-detail-container').css({ "width": "100%", "padding-right": "15px" });
            $('#summary-button').show();
        }
        else {
            $('.overlay').hide();
            $('#summary-button').hide();
            $('#hide-summary-button').hide();
            $('#job-detail-container').css({ "width": "58.33333333%", "padding-right": "7px" });
            $('#job-summary-container .job_well').css({
                'box-shadow': 'none',
                'height': 'auto'
            });
            $('#job-summary-container').css({ "width": "41.66666667%", "padding-right": "15px", "z-index": 0 }).show();
        }

        // Adjust page height
        $('#plays-table-detail').height(150);
        $('#plays-table-detail').mCustomScrollbar("update");
        $('#tasks-table-detail').height(150);
        $('#tasks-table-detail').mCustomScrollbar("update");
        $('#hosts-table-detail').height(150);
        $('#hosts-table-detail').mCustomScrollbar("update");
        height = ($('#wrap').height() - $('.site-footer').height()) - $('.main-container').height() - 22;
        if (height > 15) {
            $('#plays-table-detail').height(150 + (height / 3));
            $('#plays-table-detail').mCustomScrollbar("update");
            $('#tasks-table-detail').height(150 + (height / 3));
            $('#tasks-table-detail').mCustomScrollbar("update");
            $('#hosts-table-detail').height(150 + (height / 3));
            $('#hosts-table-detail').mCustomScrollbar("update");
        }
    }
    $(document).ready(function() {
        adjustSize();
    });

    $(window).resize(_.debounce(function(){
        adjustSize();
    }, 500));

    $scope.toggleSummary = function(hide) {
        var docw, doch, height = $('#job-detail-container').height(), slide_width;
        if (!hide) {
            docw = $(window).width();
            doch = $(window).height();
            slide_width = (docw < 840) ? '100%' : '80%';
            $('#summary-button').hide();
            $('.overlay').css({
                width: $(document).width(),
                height: $(document).height()
            }).show();
            $('#job-summary-container .job_well').height(height - 18).css({
                'box-shadow': '-3px 3px 5px 0 #ccc'
            });
            $('#hide-summary-button').show();
            $('#job-summary-container').css({
                top: 0,
                right: 0,
                width: slide_width,
                'z-index': 2000,
                'padding-right': '15px',
                'padding-left': '15px'
            }).show('slide', {'direction': 'right'});
        }
        else {
            $('.overlay').hide();
            $('#summary-button').show();
            $('#job-summary-container').hide('slide', {'direction': 'right'});
        }
    };

    $scope.HostDetailOnTotalScroll = function(mcs) {
        var url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask;
        url += '&host__name__gt=' + scope.hostResults[scope.hostResults.length - 1].name + '&host__isnull=false&page_size=5&order_by=host__name';
        if (!scope.auto_scroll) {
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    setTimeout(function() {
                        scope.$apply(function() {
                            data.results.forEach(function(row) {
                                scope.hostResults.push({
                                    id: row.id,
                                    status: ( (row.failed) ? 'failed': (row.changed) ? 'changed' : 'successful' ),
                                    host_id: row.host,
                                    task_id: row.parent,
                                    name: row.event_data.host,
                                    created: row.created,
                                    msg: ( (row.event_data && row.event_data.res) ? row.event_data.res.msg : '' )
                                });
                                if (scope.hostResults.length > 10) {
                                    scope.hostResults.splice(0,1);
                                }
                            });
                            //$('#hosts-table-detail').mCustomScrollbar("update");
                            if (data.next) {
                                // there are more rows. move dragger up, letting user know.
                                setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop - 10) + 'px'}); }, 700);
                            }
                        });
                    }, 100);
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        scope.auto_scroll = false;
    };

    $scope.HostDetailOnTotalScrollBack = function(mcs) {
        var url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask;
        Wait('start');
        url += '&host__name__lt=' + scope.hostResults[0].name + '&host__isnull=false&page_size=5&order_by=-host__name';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                setTimeout(function() {
                    scope.$apply(function() {
                        data.results.forEach(function(row) {
                            scope.hostResults.unshift({
                                id: row.id,
                                status: ( (row.failed) ? 'failed': (row.changed) ? 'changed' : 'successful' ),
                                host_id: row.host,
                                task_id: row.parent,
                                name: row.event_data.host,
                                created: row.created,
                                msg: ( (row.event_data && row.event_data.res) ? row.event_data.res.msg : '' )
                            });
                            if (scope.hostResults.length > 10) {
                                scope.hostResults.pop();
                            }
                        });
                        $('#hosts-table-detail').mCustomScrollbar("update");
                        if (data.next) {
                            // there are more rows. move dragger down, letting user know.
                            setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop + 10) + 'px' }); }, 700);
                        }
                    });
                }, 100);
                Wait('stop');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };

    $scope.HostSummaryOnTotalScroll = function(mcs) {
        var url = GetBasePath('jobs') + job_id + '/job_host_summaries/';
        url += '?host__name__gt=' + scope.hosts[scope.hosts.length - 1].name + '&page_size=5&order_by=host__name';
        if (!scope.auto_scroll) {
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    setTimeout(function() {
                        scope.$apply(function() {
                            data.results.forEach(function(row) {
                                scope.hosts.push({
                                    id: row.host,
                                    name: row.summary_fields.host.name,
                                    ok: row.ok,
                                    changed: row.changed,
                                    unreachable: row.dark,
                                    failed: row.failures
                                });
                                if (scope.hosts.length > 10) {
                                    scope.hosts.splice(0,1);
                                }
                            });
                            //$('#hosts-summary-table').mCustomScrollbar("update");
                            if (data.next) {
                                // there are more rows. move dragger up, letting user know.
                                setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop - 10) + 'px'}); }, 700);
                            }
                        });
                    }, 100);
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        scope.auto_scroll = false;
    };

    $scope.HostSummaryOnTotalScrollBack = function(mcs) {
        var url = GetBasePath('jobs') + job_id + '/job_host_summaries/';
        Wait('start');
        url += '?host__name__lt=' + scope.hosts[0].name + '&page_size=5&order_by=-host__name';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                setTimeout(function() {
                    scope.$apply(function() {
                        data.results.forEach(function(row) {
                            scope.hosts.unshift({
                                id: row.host,
                                name: row.summary_fields.host.name,
                                ok: row.ok,
                                changed: row.changed,
                                unreachable: row.dark,
                                failed: row.failures
                            });
                            if (scope.hosts.length > 10) {
                                scope.hosts.pop();
                            }
                        });
                        $('#hosts-summary-table').mCustomScrollbar("update");
                        if (data.next) {
                            // there are more rows. move dragger down, letting user know.
                            setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop + 10) + 'px' }); }, 700);
                        }
                    });
                }, 100);
                Wait('stop');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };

    $scope.searchTaskHosts = function() {
        var url;
        Wait('start');
        scope.hostResults = [];
        url = GetBasePath('jobs') + $routeParams.id + '/job_events/?parent=' + scope.activeTask;
        url += (scope.task_host_name) ? '&host__name__icontains=' + scope.task_host_name : '';
        url += '&host__name__isnull=false&page_size=10&order_by=host__name';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                var i;
                for (i = 0;  i < data.results.length; i++) {
                    scope.hostResults.push({
                        id: data.results[i].id,
                        status: ( (data.results[i].failed) ? 'failed' : (data.results[i].changed) ? 'changed' : 'successful' ),
                        host_id: data.results[i].host,
                        task_id: data.results[i].parent,
                        name: data.results[i].summary_fields.host.name,
                        created: data.results[i].created,
                        msg: data.results[i].event_data.res.msg
                    });
                }
                Wait('stop');
                SelectHost({ scope: scope });
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
        if (scope.task_host_name) {
            scope.searchTaskHostsEnabled = false;
        }
        else {
            scope.searchTaskHostsEnabled = true;
        }
    };

    $scope.taskHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            $scope.searchTaskHosts();
        }
    };

    $scope.searchSummaryHosts = function() {
        var url;
        Wait('start');
        scope.hosts = [];
        url = GetBasePath('jobs') + $routeParams.id + '/job_host_summaries/?';
        url += (scope.summary_host_name) ? 'host__name__icontains=' + scope.summary_host_name + '&': '';
        url += 'page_size=10&order_by=host__name';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                data.results.forEach(function(row) {
                    scope.hosts.push({
                        id: row.host,
                        name: row.summary_fields.host.name,
                        ok: row.ok,
                        changed: row.changed,
                        unreachable: row.dark,
                        failed: row.failures
                    });
                });
                Wait('stop');
                $('#hosts-summary-table').mCustomScrollbar("update");
                scope.auto_scroll = true;
                setTimeout( function() { $('#hosts-summary-table').mCustomScrollbar("scrollTo", "bottom"); }, 700);
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
        if (scope.summary_host_name) {
            scope.searchSummaryHostsEnabled = false;
        }
        else {
            scope.searchSummaryHostsEnabled = true;
        }
    };

    $scope.summaryHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            $scope.searchSummaryHosts();
        }
    };
}

JobDetailController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'GetBasePath', 'Wait',
    'Rest', 'ProcessErrors', 'DigestEvents', 'SelectPlay', 'SelectTask', 'Socket', 'GetElapsed', 'SelectHost'
];
