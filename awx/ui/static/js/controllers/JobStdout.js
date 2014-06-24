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
        first_time=0;

    event_socket = Socket({
        scope: $scope,
        endpoint: "job_events"
    });

    Wait('start');

    event_socket.init();

    event_socket.on("job_events-" + job_id, function() {
        if (api_complete) {
            $scope.$emit('LoadStdout');
        }
    });

    if ($scope.removeLoadStdout) {
        $scope.removeLoadStdout();
    }
    $scope.removeLoadStdout = $scope.$on('LoadStdout', function() {
        Rest.setUrl(stdout_url + '?format=json&start_line=-500');
        Rest.get()
            .success(function(data) {
                api_complete = true;
                Wait('stop');
                $('#pre-container-content').html(data.content);
                current_range = data.range;
                //$('#pre-container').mCustomScrollbar("update");
                setTimeout(function() {
                    $('#pre-container').mCustomScrollbar("scrollTo", 'bottom');
                }, 300);
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    });

    function resizeToFit() {
        available_height = $(window).height() - $('#main-menu-container .navbar').outerHeight() -
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
            $scope.$emit('LoadStdout');
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + job_id + '. GET returned: ' + status });
        });


    $scope.onTotalScroll = function() {
        $log.debug('Total scroll!');
    };

    $scope.onTotalScrollBack = function() {
        // scroll up or back in time toward the beginning of the file
        if (current_range.start > 0) {
            //we haven't hit the top yet
            var start = (current_range.start < 500) ? 0 : current_range.start - 500,
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
}

JobStdoutController.$inject = [ '$log', '$rootScope', '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors',
    'Socket' ];

