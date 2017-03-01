/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$log', '$rootScope', '$scope', '$state', '$stateParams', 'ProcessErrors', 'Rest', 'Wait',
    function ($log, $rootScope, $scope, $state, $stateParams, ProcessErrors, Rest, Wait) {

        var api_complete = false,
            current_range,
            loaded_sections = [],
            event_queue = 0,
            auto_scroll_down=true,  // programmatic scroll to bottom
            live_event_processing = true,
            page_size = 500,
            job_id = $stateParams.id;

        $scope.should_apply_live_events = true;

        // Open up a socket for events depending on the type of job
        function openSockets() {
            if ($state.current.name === 'jobResult') {
               $log.debug("socket watching on job_events-" + job_id);
               $scope.$on(`ws-job_events-${job_id}`, function() {
                   $log.debug("socket fired on job_events-" + job_id);
                   if (api_complete) {
                       event_queue++;
                   }
               });
            }
            if ($state.current.name === 'adHocJobStdout') {
                $log.debug("socket watching on ad_hoc_command_events-" + job_id);
                $scope.$on(`ws-ad_hoc_command_events-${job_id}`, function() {
                    $log.debug("socket fired on ad_hoc_command_events-" + job_id);
                    if (api_complete) {
                        event_queue++;
                    }
                });
            }
        }

        openSockets();

        // This is a trigger for loading up the standard out
        if ($scope.removeLoadStdout) {
            $scope.removeLoadStdout();
        }
        $scope.removeLoadStdout = $scope.$on('LoadStdout', function() {
            if (loaded_sections.length === 0) {
                loadStdout();
            }
            else if (live_event_processing) {
                getNextSection();
            }
        });

        // This interval checks to see whether or not we've gotten a new
        // event via sockets.  If so, go out and update the standard out
        // log.
        $rootScope.jobStdOutInterval = setInterval( function() {
            if (event_queue > 0) {
                // events happened since the last check
                $log.debug('checking for stdout...');
                if (loaded_sections.length === 0) { ////this if statement for refresh
                    $log.debug('calling LoadStdout');
                    loadStdout();
                }
                else if (live_event_processing) {
                    $log.debug('calling getNextSection');
                    getNextSection();
                }
                event_queue = 0;
            }
        }, 2000);

        // stdoutEndpoint gets passed through in the directive declaration.
        // This watcher fires off loadStdout() when the endpoint becomes
        // available.
        $scope.$watch('stdoutEndpoint', function(newVal, oldVal) {
            if(newVal && newVal !== oldVal) {
                // Fire off the server call
                loadStdout();
            }
        });

        // stdoutText optionall gets passed through in the directive declaration.
        $scope.$watch('stdoutText', function(newVal, oldVal) {
            if(newVal && newVal !== oldVal) {
                $('#pre-container-content').html(newVal);
            }
        });

        function loadStdout() {
            if (!$scope.stdoutEndpoint) {
                return;
            }

            Rest.setUrl($scope.stdoutEndpoint + '?format=json&start_line=0&end_line=' + page_size);
            Rest.get()
                .success(function(data) {
                    Wait('stop');
                    if (data.content) {
                        api_complete = true;
                        $('#pre-container-content').html(data.content);
                        current_range = data.range;
                        if (data.content !== "Waiting for results...") {
                            loaded_sections.push({
                                start: (data.range.start < 0) ? 0 : data.range.start,
                                end: data.range.end
                            });
                        }

                        $('#pre-container').scrollTop($('#pre-container').prop("scrollHeight"));
                    }
                    else {
                        api_complete = true;
                    }
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }

        function getNextSection() {
            if (!$scope.stdoutEndpoint) {
                return;
            }

            // get the next range of data from the API
            var start = loaded_sections[loaded_sections.length - 1].end, url;
            url = $scope.stdoutEndpoint + '?format=json&start_line=' + start + '&end_line=' + (start + page_size);
            $('#stdoutMoreRowsBottom').fadeIn();
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    if ($('#pre-container-content').html() === "Waiting for results...") {
                        $('#pre-container-content').html(data.content);
                    } else {
                        $('#pre-container-content').append(data.content);
                    }
                    loaded_sections.push({
                        start: (data.range.start < 0) ? 0 : data.range.start,
                        end: data.range.end
                    });
                    if ($scope.should_apply_live_events) {
                        // if user has not disabled live event view by scrolling upward, then scroll down to the new content
                        current_range = data.range;
                        auto_scroll_down = true; // prevent auto load from happening
                        $('#pre-container').scrollTop($('#pre-container').prop("scrollHeight"));
                    }
                    $('#stdoutMoreRowsBottom').fadeOut(400);
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                });
        }

        // lrInfiniteScroll handler
        // grabs the next stdout section
        $scope.stdOutGetNextSection = function(){
            if (current_range.absolute_end > current_range.end){
                var url = $scope.stdoutEndpoint + '?format=json&start_line=' + current_range.end +
                    '&end_line=' + (current_range.end + page_size);
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data){
                        $('#pre-container-content').append(data.content);
                        current_range = data.range;
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
                    });
            }
        };

        // We watch for job status changes here.  If the job completes we want to clear out the
        // stdout interval and kill the live_event_processing flag.
        $scope.$on(`ws-jobs`, function(e, data) {
            if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10)) {
                if (data.status === 'failed' || data.status === 'canceled' ||
                        data.status === 'error' || data.status === 'successful') {
                    if ($rootScope.jobStdOutInterval) {
                        window.clearInterval($rootScope.jobStdOutInterval);
                    }
                    if (live_event_processing) {
                        if (loaded_sections.length === 0) {
                            loadStdout();
                        }
                        else {
                            getNextSection();
                        }
                    }
                    live_event_processing = false;
                }
            }
        });

}];
