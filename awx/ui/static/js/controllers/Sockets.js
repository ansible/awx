/************************************
* Copyright (c) 2014 AnsibleWorks, Inc.
*
*  Sockets.js
*  SocketsController- simple test of socket connection
*
*/

'use strict';

function SocketsController ($scope, $compile, ClearScope, Socket) {

    ClearScope();

    var test_scope = $scope.$new(),
        jobs_scope = $scope.$new(),
        job_events_scope = $scope.$new(),
        schedules_scope = $scope.$new(),
        test_socket = Socket({ scope: test_scope, endpoint: "test" }),
        jobs_socket = Socket({ scope: jobs_scope, endpoint: "jobs" }),
        schedules_socket = Socket({ scope: schedules_scope, endpoint: "schedules" }),
        job_events_socket = Socket({ scope: job_events_scope, endpoint: "job_events" }),
        e, html;

    test_scope.messages = [];
    jobs_scope.messages = [];
    schedules_scope.messages = [];
    job_events_scope.messages = [];

    html = "<div class=\"section-title\"><strong>Socket url</strong>: {{ socket_url }} &nbsp;<strong>Status:</strong> {{ socket_status }} {{ socket_reason }}</div>\n" +
        "<div class=\"message-title\">\n" +
        "<h5>Received Messages:</h5>\n" +
        "</div>\n" +
        "<div class=\"well message-section\">\n" +
        "<ul>\n" +
        "<li ng-repeat=\"message in messages\">{{ message }} </li>\n" +
        "</ul>\n" +
        "</div>\n";

    e = angular.element(document.getElementById('test-container'));
    e.append(html);
    $compile(e)(test_scope);
    e = angular.element(document.getElementById('schedules-container'));
    e.append(html);
    $compile(e)(schedules_scope);
    e = angular.element(document.getElementById('jobs-container'));
    e.append(html);
    $compile(e)(jobs_scope);

    html = "<div class=\"row events-section\">\n" +
            "<div class=\"col-md-6\">\n" +
            "<div class=\"section-title\"><strong>Socket url</strong>: {{ socket_url }} &nbsp;<strong>Status:</strong> {{ socket_status }} {{ socket_reason }}</div>\n" +
            "</div>\n" +
            "<div class=\"col-md-6\">\n" +
            "<form class=\"form-inline\">\n" +
                "<div class=\"form-group\">\n" +
                   "<label for=\"job_id\">Job Id</label>\n" +
                   "<input type=\"text\" name=\"job_id\" id=\"job_id\" ng-model=\"job_id\" class=\"input-sm form-control\">\n" +
                "</div>\n" +
                "<button type=\"submit\" ng-disabled=\"!job_id\" ng-click=\"subscribeToJobEvent()\" class=\"btn btn-sm btn-primary\"><i class=\"fa fa-check\"></i> Subscribe</button>\n" +
            "</form>\n" +
            "</div>\n" +
            "</div>\n" +
            "<div class=\"message-title\">" +
            "<p>Subscribed to events for job: {{ jobs_list }}</p>\n" +
            "<h5>Received Messages:</h5>\n" +
            "</div>\n" +
            "<div class=\"well message-section\" id=\"event-message-container\">\n" +
               "<ul>\n" +
                  "<li ng-repeat=\"message in messages\">{{ message }} </li>\n" +
               "</ul>\n" +
            "</div>\n";

    e = angular.element(document.getElementById('job-events-container'));
    e.append(html);
    $compile(e)(job_events_scope);

    schedules_socket.init();
    test_socket.init();
    jobs_socket.init();
    job_events_socket.init();

    schedules_scope.url = schedules_socket.getUrl();
    test_scope.url = test_socket.getUrl();
    jobs_scope.url = jobs_socket.getUrl();
    job_events_scope.url = job_events_socket.getUrl();

    test_scope.messages.push('Message Displayed Before Connection');

    test_socket.on('test', function(data) {
        test_scope.messages.push(data);
    });

    schedules_socket.on("schedule_changed", function(data) {
        schedules_scope.messages.push(data);
    });

    jobs_socket.on("status_changed", function(data) {
        jobs_scope.messages.push(data);
    });

    jobs_socket.on("summary_complete", function(data) {
        jobs_scope.messages.push(data);
    });

    job_events_scope.jobs_list = [];

    job_events_scope.subscribeToJobEvent = function() {
        job_events_scope.jobs_list.push(job_events_scope.job_id);
        job_events_socket.on("job_events-" + job_events_scope.job_id, function(data) {
            job_events_scope.messages.push(data);
            setTimeout(function() {
                $(document).scrollTop($(document).prop("scrollHeight"));
                $('#event-message-container').scrollTop($('#event-message-container').prop("scrollHeight"));
            }, 300);
        });
    };
}

SocketsController.$inject = [ '$scope', '$compile', 'ClearScope', 'Socket'];
