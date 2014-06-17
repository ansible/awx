/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobStdout.js
 *
 */

'use strict';

function JobStdoutController ($rootScope, $scope, $compile, $routeParams, ClearScope, GetBasePath, Wait, Rest, ProcessErrors, Socket) {

    ClearScope();

    var available_height, job_id = $routeParams.id,
        api_complete = false,
        stdout_url,
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
        Rest.setUrl(stdout_url + '?format=html');
        Rest.get()
            .success(function(data) {
                var lines, styles=[], html=[], found=false, doc, style, pre, parser;
                api_complete = true;
                Wait('stop');
                if ($rootScope.browser === "SAFARI") {
                    // Safari's DOMParser will not parse HTML, so we have to do our best to extract the
                    // parts we want.

                    lines = data.split("\n");
                    // Get the style sheet
                    lines.forEach(function(line) {
                        if (/<style.*/.test(line)) {
                            found = true;
                        }
                        if (found) {
                            styles.push(line);
                        }
                        if (/<\/style>/.test(line)) {
                            found = false;
                        }
                    });
                    found = false;
                    // Get all the bits between <pre> and  </pre>
                    lines.forEach(function(line) {
                        if (/<pre>/.test(line)) {
                            found = true;
                        }
                        else if (/<\/pre>/.test(line)) {
                            found = false;
                        }
                        else if (found) {
                            html.push(line);
                        }
                    });
                    $('#style-sheet-container').empty().html(styles.join("\n"));
                    $('#pre-container-content').empty().html(html.join("\n"));
                }
                else {
                    parser = new DOMParser();
                    doc = parser.parseFromString(data, "text/html");
                    pre = doc.getElementsByTagName('pre');
                    style = doc.getElementsByTagName('style');
                    $('#style-sheet-container').empty().html(style[0]);
                    $('#pre-container-content').empty().html($(pre[0]).html());
                }
                setTimeout(function() { $('#pre-container').mCustomScrollbar("scrollTo", 'bottom'); }, 1000);
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    });

    function resizeToFit() {
        available_height = $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() -
            $('#breadcrumb-container').outerHeight() - $('.site-footer').outerHeight() * 2;
        if ($(window).width() < 768) {
            available_height += 55;
        }
        else if ($(window).width() > 1240) {
            available_height += 5;
        }
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
}

JobStdoutController.$inject = [ '$rootScope', '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors', 'Socket' ];

