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
        first_time=0,
        loaded_sections = [],
        event_queue = 0,
        auto_scroll_down=true,
        live_event_processing = true,
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
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10)) {
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
        // limit the scrolling to every 5 seconds
        $log.debug('checking for stdout...');
        if (event_queue > 15) {
            if (loaded_sections.length === 0) {
                $log.debug('calling LoadStdout');
                $scope.$emit('LoadStdout');
            }
            else {
                $log.debug('calling getNextSection');
                getNextSection();
            }
            event_queue = 0;
        }
    }, 5000);

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
                    loaded_sections.push(data.range.start);
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
            $('#breadcrumb-container').outerHeight() - 20;
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
            }
            $scope.$emit('LoadStdout');
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + job_id + '. GET returned: ' + status });
        });


    $scope.onTotalScroll = function() {
        // scroll forward or into the future toward the end of the file
        var start = current_range.end + 1, url;
        if ((!live_event_processing) && (!auto_scroll_down) && loaded_sections.indexOf(start) < 0) {
            url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (current_range.start + page_size);
            first_time++;
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    Wait('stop');
                    if (data.content) {
                        $('#pre-container-content').append(data.content);
                        loaded_sections.push(data.range.start);
                        current_range = data.range;
                    }
                    //$("#pre-container").mCustomScrollbar("scrollTo", "bottom", {scrollInertia:0});
                    //$('#pre-container').mCustomScrollbar("update");
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
        if ((!live_event_processing) && current_range.start > 0) {
            //we haven't hit the top yet
            var start = (current_range.start < page_size) ? 0 : current_range.start - page_size,
                url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (current_range.start - 1);
            first_time++;
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    Wait('stop');
                    var oldContentHeight, heightDiff;
                    oldContentHeight=$("#pre-container .mCSB_container").innerHeight();
                    $('#pre-container-content').prepend(data.content);
                    loaded_sections.unshift(data.range.start);
                    current_range = data.range;
                    heightDiff=$("#pre-container .mCSB_container").innerHeight() - oldContentHeight;
                    if (first_time === 1) {
                        //setTimeout(function() { $("#pre-container").mCustomScrollbar("scrollTo", heightDiff, {scrollInertia:0}); }, 300);
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

    function getNextSection() {
        var start = current_range.end + 1, url;
        if (loaded_sections.indexOf(start) < 0) {
            url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (current_range.start + page_size);
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    Wait('stop');
                    $('#pre-container-content').append(data.content);
                    loaded_sections.push(data.range.start);
                    current_range = data.range;
                    $("#pre-container").mCustomScrollbar("scrollTo", "bottom", {scrollInertia:0});
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }
    }

}

JobStdoutController.$inject = [ '$log', '$rootScope', '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors',
    'Socket' ];

