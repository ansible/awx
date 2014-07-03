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
        status_socket,
        loaded_sections = [],
        event_queue = 0,
        auto_scroll_down=true,  // programmatic scroll to bottom
        live_event_processing = true,
        should_apply_live_events = true,
        page_size = 500,
        lastScrollTop = 0,
        st,
        direction;

    status_socket = Socket({
        scope: $scope,
        endpoint: "jobs"
    });
    status_socket.init();
    status_socket.on("status_changed", function(data) {
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10) && $scope.job) {
            $scope.job.status = data.status;
            if (data.status === 'failed' || data.status === 'canceled' ||
                    data.status === 'error' || data.status === 'successful') {
                if ($rootScope.jobStdOutInterval) {
                    window.clearInterval($rootScope.jobStdOutInterval);
                }
                if (live_event_processing) {
                    if (loaded_sections.length === 0) {
                        $scope.$emit('LoadStdout');
                    }
                    else {
                        getNextSection();
                    }
                }
                live_event_processing = false;
            }
        }
    });

    event_socket = Socket({
        scope: $scope,
        endpoint: "job_events"
    });
    event_socket.init();
    event_socket.on("job_events-" + job_id, function() {
        if (api_complete) {
            event_queue++;
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
                    $('#pre-container').scrollTop($('#pre-container').prop("scrollHeight"));
                    //console.log($('#pre-container-content').prop("scrollHeight"));
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

    function detectDirection() {
        st = $('#pre-container').scrollTop();
        if (st > lastScrollTop) {
            direction = "down";
        } else {
            direction = "up";
        }
        lastScrollTop = st;
        return  direction;
    }

    function resizeToFit() {
        available_height = $(window).height() - $('#main-menu-container .navbar').outerHeight() - $('#job-status').outerHeight() -
            $('#breadcrumb-container').outerHeight() - 60;
        $('#pre-container').height(available_height);
    }
    resizeToFit();

    $(window).resize(_.debounce(function() {
        resizeToFit();
    }, 500));

    $('#pre-container').bind('scroll', function() {
        if (detectDirection() === "up") {
            should_apply_live_events = false;
        }
    });

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


    $scope.stdOutScrollToTop = function() {
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
            $('#stdoutMoreRowsTop').fadeIn();
            url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + end;
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    //var currentPos = $('#pre-container').scrollTop();
                    var newSH, oldSH = $('#pre-container').prop('scrollHeight'),
                        st = $('#pre-container').scrollTop();

                    $('#pre-container-content').prepend(data.content);

                    newSH = $('#pre-container').prop('scrollHeight');
                    $('#pre-container').scrollTop(newSH - oldSH + st);

                    loaded_sections.unshift({
                        start: (data.range.start < 0) ? 0 : data.range.start,
                        end: data.range.end
                    });
                    current_range = data.range;
                    $('#stdoutMoreRowsTop').fadeOut(400);
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }
    };

    function getNextSection() {
        // get the next range of data from the API
        var start = loaded_sections[loaded_sections.length - 1].end + 1, url;
        url = stdout_url + '?format=json&start_line=' + start + '&end_line=' + (start + page_size);
        $('#stdoutMoreRowsBottom').fadeIn();
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
                    $('#pre-container-content').scrollTop($('#pre-container-content').prop("scrollHeight"));
                }
                $('#stdoutMoreRowsBottom').fadeOut(400);
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    }

}

JobStdoutController.$inject = [ '$log', '$rootScope', '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors',
    'Socket' ];

