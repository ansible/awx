/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 */

'use strict';

function JobDetailController ($scope, $compile, $routeParams, ClearScope, Breadcrumbs, LoadBreadCrumbs, GetBasePath, Wait, Rest, ProcessErrors, DigestEvents,
    SelectPlay, SelectTask, Socket, GetElapsed, SelectHost, FilterAllByHostName) {

    ClearScope();

    var job_id = $routeParams.id,
        event_socket, job,
        event_queue = [],
        processed_events = [],
        scope = $scope,
        api_complete = false,
        refresh_count = 0;
    
    scope.plays = [];
    scope.tasks = [];
    scope.hosts = [];
    scope.search_all_tasks = [];
    scope.search_all_plays = [];
    scope.hostResults = [];
    scope.job_status = {};
    scope.job_id = job_id;
    scope.auto_scroll = false;
    scope.searchTaskHostsEnabled = true;
    scope.searchSummaryHostsEnabled = true;
    scope.hostTableRows = 300;
    scope.hostSummaryTableRows = 300;
    scope.searchAllHostsEnabled = true;

    scope.eventsHelpText = "<p><i class=\"fa fa-circle successful-hosts-color\"></i> Successful</p>\n" +
        "<p><i class=\"fa fa-circle changed-hosts-color\"></i> Changed</p>\n" +
        "<p><i class=\"fa fa-circle unreachable-hosts-color\"></i> Unreachable</p>\n" +
        "<p><i class=\"fa fa-circle failed-hosts-color\"></i> Failed</p>\n";

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
    
    
    if (scope.removeLoadJob) {
        scope.removeLoadJob();
    }
    scope.removeLoadJobRow = scope.$on('LoadJob', function() {
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
                scope.job_status.status = (data.status === 'waiting' || data.status === 'new') ? 'pending' : data.status;
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

                scope.setSearchAll('host');
                scope.$emit('JobReady', data.related.job_events + '?page_size=50&order_by=id');
                scope.$emit('GetCredentialNames', data);
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET returned: ' + status });
            });
    });

    if (scope.removeRefreshCompleted) {
        scope.removeRefreshCompleted();
    }
    scope.removeRefreshCompleted = scope.$on('RefreshCompleted', function() {
        refresh_count++;
        if (refresh_count === 1) {
            // First time. User just loaded page.
            scope.$emit('LoadJob');
        }
    });

    scope.adjustSize = function() {
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
        // Detail table height adjusting. First, put page height back to 'normal'.
        $('#plays-table-detail').height(150);
        $('#plays-table-detail').mCustomScrollbar("update");
        $('#tasks-table-detail').height(150);
        $('#tasks-table-detail').mCustomScrollbar("update");
        $('#hosts-table-detail').height(150);
        $('#hosts-table-detail').mCustomScrollbar("update");
        height = $('#wrap').height() - $('.site-footer').outerHeight() - $('.main-container').height();
        if (height > 15) {
            // there's a bunch of white space at the bottom, let's use it
            $('#plays-table-detail').height(150 + (height / 3));
            $('#plays-table-detail').mCustomScrollbar("update");
            $('#tasks-table-detail').height(150 + (height / 3));
            $('#tasks-table-detail').mCustomScrollbar("update");
            $('#hosts-table-detail').height(150 + (height / 3));
            $('#hosts-table-detail').mCustomScrollbar("update");
        }
        // Summary table height adjusting.
        height = ($('#job-detail-container').height() / 2) - $('#hosts-summary-section .header').outerHeight() -
            $('#hosts-summary-section .table-header').outerHeight() -
            $('#summary-search-section').outerHeight() - 20;
        $('#hosts-summary-table').height(height);
        $('#hosts-summary-table').mCustomScrollbar("update");
        scope.$emit('RefreshCompleted');
    };

    /*function refreshHostRows() {
        var url;
        if (scope.activeTask) {
            scope.hostResults = [];
            scope.auto_scroll = true;
            url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask + '&';
            url += (scope.task_host_name) ? 'host__name__icontains=' + scope.task_host_name + '&' : '';
            url += 'host__isnull=false&page_size=' + scope.hostTableRows + '&order_by=host__name';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
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
                    });
                    $('#hosts-table-detail').mCustomScrollbar("update");
                    setTimeout( function() { $('#hosts-table-detail').mCustomScrollbar("scrollTo", "bottom"); }, 700);
                    Wait('stop');
                    scope.$emit('RefreshCompleted');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            $('#hosts-table-detail').mCustomScrollbar("update");
            scope.$emit('RefreshCompleted');
        }
    }

    function refreshSummaryHostRows() {
        if (scope.hosts.length < scope.hostSummaryTableRows) {
            var url = GetBasePath('jobs') + job_id + '/job_host_summaries/?';
            url += (scope.summary_host_name) ? 'host__name__icontains=' + scope.summary_host_name + '&': '';
            url += '&page_size=' + scope.hostSummaryTableRows + '&order_by=host__name';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    data.results.forEach(function(row) {
                        var found = false;
                        scope.hosts.every(function(host) {
                            if (host.id === row.host) {
                                found = true;
                                return false;
                            }
                            return true;
                        });
                        if (!found) {
                            scope.hosts.push({
                                id: row.host,
                                name: row.summary_fields.host.name,
                                ok: row.ok,
                                changed: row.changed,
                                unreachable: row.dark,
                                failed: row.failures
                            });
                        }
                    });
                    scope.hosts.sort(function(a,b) {
                        if (a.name < b.name) {
                            return -1;
                        }
                        if (a.name > b.name) {
                            return 1;
                        }
                        return 0;
                    });
                    $('#hosts-summary-table').mCustomScrollbar("update");
                    setTimeout( function() { $('#hosts-summary-table').mCustomScrollbar("scrollTo", "bottom"); }, 700);
                    Wait('stop');
                    scope.$emit('RefreshCompleted');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            $('#hosts-table-detail').mCustomScrollbar("update");
            scope.$emit('RefreshCompleted');
        }
    }*/

    setTimeout(function() { scope.adjustSize(); }, 500);

    // Use debounce for the underscore library to adjust after user resizes window.
    $(window).resize(_.debounce(function(){
        scope.adjustSize();
    }, 500));

    scope.setSearchAll = function(search) {
        if (search === 'host') {
            scope.search_all_label = 'Host';
            scope.searchAllDisabled = false;
            scope.search_all_placeholder = 'Search all by host name';
        }
        else {
            scope.search_all_label = 'Failures';
            scope.search_all_placeholder = 'Show failed events';
            scope.searchAllDisabled = true;
            scope.search_all_placeholder = '';
        }
    };

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

    scope.toggleSummary = function(hide) {
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

    scope.HostDetailOnTotalScroll = _.debounce(function() {
        // Called when user scrolls down (or forward in time). Using _.debounce
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if (!scope.auto_scroll && scope.activeTask && scope.hostResults.length) {
                scope.auto_scroll = true;
                url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask + '&';
                url += (scope.task_host_name) ? 'host__name__icontains=' + scope.task_host_name + '&' : '';
                url += 'host__name__gt=' + scope.hostResults[scope.hostResults.length - 1].name + '&host__isnull=false&page_size=' + (scope.hostTableRows / 3) + '&order_by=host__name';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
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
                            if (scope.hostResults.length > scope.hostTableRows) {
                                scope.hostResults.splice(0,1);
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger up, letting user know.
                            setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop - 15) + 'px'}); }, 700);
                        }
                        scope.auto_scroll = false;
                        Wait('stop');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
            else {
                scope.auto_scroll = false;
            }
        });
    }, 300);

    scope.HostDetailOnTotalScrollBack = _.debounce(function() {
        // Called when user scrolls up (or back in time)
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if (!scope.auto_scroll && scope.activeTask && scope.hostResults.length) {
                scope.auto_scroll = true;
                url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask + '&';
                url += (scope.task_host_name) ? 'host__name__icontains=' + scope.task_host_name + '&' : '';
                url += 'host__name__lt=' + scope.hostResults[0].name + '&host__isnull=false&page_size=' + (scope.hostTableRows / 3) + '&order_by=-host__name';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
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
                            if (scope.hostResults.length > scope.hostTableRows) {
                                scope.hostResults.pop();
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger down, letting user know.
                            setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop + 15) + 'px' }); }, 700);
                        }
                        Wait('stop');
                        scope.auto_scroll = false;
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
            else {
                scope.auto_scroll = false;
            }
        });
    }, 300);

    scope.HostSummaryOnTotalScroll = function(mcs) {
        var url;
        if (!scope.auto_scroll && scope.hosts) {
            url = GetBasePath('jobs') + job_id + '/job_host_summaries/?';
            url += (scope.summary_host_name) ? 'host__name__icontains=' + scope.summary_host_name + '&': '';
            url += 'host__name__gt=' + scope.hosts[scope.hosts.length - 1].name + '&page_size=' + (scope.hostSummaryTableRows / 3) + '&order_by=host__name';
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
                                if (scope.hosts.length > scope.hostSummaryTableRows) {
                                    scope.hosts.splice(0,1);
                                }
                            });
                            if (data.next) {
                                // there are more rows. move dragger up, letting user know.
                                setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop - 15) + 'px'}); }, 700);
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
        else {
            scope.auto_scroll = false;
        }
    };

    scope.HostSummaryOnTotalScrollBack = function(mcs) {
        var url;
        if (!scope.auto_scroll && scope.hosts) {
            url = GetBasePath('jobs') + job_id + '/job_host_summaries/?';
            url += (scope.summary_host_name) ? 'host__name__icontains=' + scope.summary_host_name + '&': '';
            url += 'host__name__lt=' + scope.hosts[0].name + '&page_size=' + (scope.hostSummaryTableRows / 3) + '&order_by=-host__name';
            Wait('start');
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
                                if (scope.hosts.length > scope.hostSummaryTableRows) {
                                    scope.hosts.pop();
                                }
                            });
                            if (data.next) {
                                // there are more rows. move dragger down, letting user know.
                                setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop + 15) + 'px' }); }, 700);
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
        else {
            scope.auto_scroll = false;
        }
    };

    scope.searchTaskHosts = function() {
        var url;
        Wait('start');
        scope.hostResults = [];
        url = GetBasePath('jobs') + $routeParams.id + '/job_events/?parent=' + scope.activeTask;
        url += (scope.task_host_name) ? '&host__name__icontains=' + scope.task_host_name : '';
        url += '&host__name__isnull=false&page_size=' + scope.hostTableRows + '&order_by=host__name';
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

    scope.taskHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchTaskHosts();
        }
    };

    scope.searchSummaryHosts = function() {
        var url;
        Wait('start');
        scope.hosts = [];
        url = GetBasePath('jobs') + $routeParams.id + '/job_host_summaries/?';
        url += (scope.summary_host_name) ? 'host__name__icontains=' + scope.summary_host_name + '&': '';
        url += 'page_size=' + scope.hostSummaryTableRows + '&order_by=host__name';
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
                setTimeout( function() {
                    scope.auto_scroll = true;
                    $('#hosts-summary-table').mCustomScrollbar("scrollTo", "bottom");
                }, 700);
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

    scope.summaryHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchSummaryHosts();
        }
    };

    scope.searchAllByHost = function() {
        if (scope.search_all_hosts_name) {
            FilterAllByHostName({
                scope: scope,
                host: scope.search_all_hosts_name
            });
            scope.searchAllHostsEnabled = false;
        }
        else {
            scope.search_all_tasks = [];
            scope.search_all_plays = [];
            scope.searchAllHostsEnabled = true;
        }
        scope.task_host_name = scope.search_all_hosts_name;
        scope.searchTaskHosts();
        scope.summary_host_name = scope.search_all_hosts_name;
        scope.searchSummaryHosts();
    };

    scope.allHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchAllByHost();
        }
    };
}

JobDetailController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'GetBasePath', 'Wait',
    'Rest', 'ProcessErrors', 'DigestEvents', 'SelectPlay', 'SelectTask', 'Socket', 'GetElapsed', 'SelectHost', 'FilterAllByHostName'
];
