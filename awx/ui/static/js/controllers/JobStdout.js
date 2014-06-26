/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobStdout.js
 *
 */

'use strict';

function JobStdoutController ($log, $rootScope, $scope, $compile, $routeParams, ClearScope, GetBasePath, Wait, Rest, ProcessErrors, Socket) {

    ClearScope();

    var available_height, job_id = $routeParams.id,
        api_complete = false,
        stdout_url,
        current_range,
        event_socket,
        first_time_up = 0,
        first_time_down = 0,
        loaded_sections = [],
        event_queue = 0,
        auto_scroll_down=true,  // programmatic scroll to bottom
        live_event_processing = true,
        should_apply_live_events = true,
        prior_mcs,
        page_size = 500;

    event_socket = Socket({
        scope: $scope,
        endpoint: "job_events"
    });

    Wait('start');

    event_socket.init();

    event_socket.on("job_events-" + job_id, function() {
        if (api_complete) {
            event_queue++;
        }
    });

    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function(e, data) {
        // if we receive a status change event for the current job indicating the job
        // is finished, stop event queue processing and reload
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10) && $scope.job) {
            $scope.job.status = data.status;
            if (data.status === 'failed' || data.status === 'canceled' ||
                    data.status === 'error' || data.status === 'successful') {
                if ($rootScope.jobStdOutInterval) {
                    window.clearInterval($rootScope.jobStdOutInterval);
                }
                if (live_event_processing) {
                    getNextSection();
                }
                live_event_processing = false;
            }
        }
    });

    $rootScope.jobStdOutInterval = setInterval( function() {
        if (event_queue > 0) {
            // events happened since the last check
            $log.debug('checking for stdout...');
            if (loaded_sections.length === 0) {
                $log.debug('calling LoadStdout');
                $scope.$emit('LoadStdout');
            }
            else if (live_event_processing) {
                $log.debug('calling getNextSection');
                getNextSection();
            }
            event_queue = 0;
        }
    }, 2000);

    if ($scope.removeLoadStdout) {
        $scope.removeLoadStdout();
    }
    $scope.removeLoadStdout = $scope.$on('LoadStdout', function() {
        Rest.setUrl(stdout_url + '?format=json&start_line=-' + page_size);
        Rest.get()
            .success(function(data) {
                Wait('stop');
                if (data.content) {
                    api_complete = true;
                    $('#pre-container-content').html(data.content);
                    current_range = data.range;
                    loaded_sections.push({
                        start: (data.range.start < 0) ? 0 : data.range.start,
                        end: data.range.end
                    });
                    setTimeout(function() {
                        $('#pre-container').mCustomScrollbar("scrollTo", "bottom");
                    }, 300);
                }
                else {
                    api_complete = true;
                }
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    });

    function resizeToFit() {
        available_height = $(window).height() - $('#main-menu-container .navbar').outerHeight() - $('#job-status').outerHeight() -
            $('#breadcrumb-container').outerHeight() - 30;
        $('#pre-container').height(available_height);
        $('#pre-container').mCustomScrollbar("update");
    }
    resizeToFit();

    $(window).resize(_.debounce(function() {
        resizeToFit();
    }, 500));

    Rest.setUrl(GetBasePath('jobs') + job_id + '/');
    Rest.get()
        .success(function(data) {
            $scope.job = data;
            stdout_url = data.related.stdout;
            if (data.status === 'successful' || data.status === 'failed' || data.status === 'error' || data.status === 'canceled') {
                live_event_processing = false;
                if ($rootScope.jobStdOutInterval) {
                    window.clearInterval($rootScope.jobStdOutInterval);
                }
            }
            $scope.$emit('LoadStdout');
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + job_id + '. GET returned: ' + status });
        });


    $scope.onTotalScroll = function() {
        // scroll forward or into the future toward the end of the file
        var start, url;
        if ((live_event_processing === false || (live_event_processing && should_apply_live_events === false)) &&
            auto_scroll_down === false) {

            if (loaded_sections.length > 0) {
                start = loaded_sections[loaded_sections.length - 1].end + 1;
            }
            else {
                start = 0;
            }
            url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (start + page_size);
            first_time_down++;
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    Wait('stop');
                    if (loaded_sections.indexOf(start) < 0) {
                        if (data.content) {
                            $('#pre-container-content').append(data.content);
                            loaded_sections.push({
                                start: (data.range.start < 0) ? 0 : data.range.start,
                                end: data.range.end
                            });
                            current_range = data.range;
                        }
                    }
                    if (data.range.end === data.range.absolute_end) {
                        should_apply_live_events = true;   //we're at the bottom
                        $log.debug('at the end. turned on live events');
                    }
                    auto_scroll_down = true;
                    if (first_time_down === 1) {
                        $('#pre-container').mCustomScrollbar("update");
                    }
                    $("#pre-container").mCustomScrollbar("scrollTo", "bottom", {scrollInertia:0});
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }
        else {
            auto_scroll_down = false;
        }
    };

    $scope.onTotalScrollBack = function() {
        // scroll up or back in time toward the beginning of the file
        var start, end, url;
        if (loaded_sections.length > 0 && loaded_sections[0].start > 0) {
            start = (loaded_sections[0].start - page_size > 0) ? loaded_sections[0].start - page_size : 0;
            end = loaded_sections[0].start - 1;
        }
        else if (loaded_sections.length === 0) {
            start = 0;
            end = page_size;
        }
        if (start !== undefined  && end !== undefined) {
            url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + end;
            first_time_up++;
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    Wait('stop');
                    var oldContentHeight, heightDiff;
                    oldContentHeight=$("#pre-container .mCSB_container").innerHeight();
                    $('#pre-container-content').prepend(data.content);
                    loaded_sections.unshift({
                        start: (data.range.start < 0) ? 0 : data.range.start,
                        end: data.range.end
                    });
                    current_range = data.range;
                    heightDiff=$("#pre-container .mCSB_container").innerHeight() - oldContentHeight;
                    if (first_time_up === 1) {
                        $('#pre-container').mCustomScrollbar("update");
                    }
                    $("#pre-container").mCustomScrollbar("scrollTo", heightDiff, {scrollInertia:0});
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }
    };

    $scope.whileScrolling = function(mcs) {
        var direction;
        if (prior_mcs !== undefined) {
            if (mcs.topPct < prior_mcs.topPct && prior_mcs.topPct !== 100) {
                direction = "up";
            }
            else if (mcs.topPct > prior_mcs.topPct) {
                direction = "down";
            }
            else {
                direction = "none";
            }
        }
        prior_mcs = mcs;
        if (direction === "up") {
            // user is scrollin up or back in time
            $log.debug('user scrolled up. turned off live events.');
            should_apply_live_events = false;
        }
    };

    $scope.scrollStarted = function() {
        // user touched the scroll bar. stop applying live events and forcing
        //if (auto_scroll_down === false) {
        //    should_apply_live_events = false;
        //    $log.debug('turned off live events');
        //}
        //else {
        //    auto_scroll_down = false;
        //}
    };

    function getNextSection() {
        // get the next range of data from the API
        var start = loaded_sections[loaded_sections.length - 1].end + 1, url;
        url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (start + page_size);
        Rest.setUrl(url);
        Rest.get()
            .success( function(data) {
                $('#pre-container-content').append(data.content);
                loaded_sections.push({
                    start: (data.range.start < 0) ? 0 : data.range.start,
                    end: data.range.end
                });
                if (should_apply_live_events) {
                    // if user has not disabled live event view by scrolling upward, then scroll down to the new content
                    current_range = data.range;
                    auto_scroll_down = true; // prevent auto load from happening
                    first_time_down++;
                    if (first_time_down === 1) {
                        $('#pre-container').mCustomScrollbar("update");
                    }
                    $("#pre-container").mCustomScrollbar("scrollTo", "bottom", {scrollInertia:0});
                }
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    }

}

JobStdoutController.$inject = [ '$log', '$rootScope', '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors',
    'Socket' ];

