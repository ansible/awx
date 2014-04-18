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
        test_socket = Socket({ scope: test_scope, endpoint: "test" }),
        jobs_socket = Socket({ scope: jobs_scope, endpoint: "jobs" }),
        job_events_socket = Socket({ scope: job_events_scope, endpoint: "job_events" }),
        e, html;

    test_scope.messages = [];
    jobs_scope.messages = [];
    job_events_scope.messages = [];

    html = "<div class=\"alert alert-info\"><strong>Socket url</strong>: {{ socket_url }} &nbsp;<strong>Status:</strong> {{ socket_status }} {{ socket_reason }}</div>\n" +
        "<div class=\"well\">\n" +
        "<h5>Received Messages:</h5>\n" +
        "<ul>\n" +
        "<li ng-repeat=\"message in messages\">{{ message }} </li>\n" +
        "</ul>\n" +
        "</div>\n";

    e = angular.element(document.getElementById('test-container'));
    e.append(html);
    $compile(e)(test_scope);
    e = angular.element(document.getElementById('jobs-container'));
    e.append(html);
    $compile(e)(jobs_scope);
    e = angular.element(document.getElementById('job-events-container'));
    e.append(html);
    $compile(e)(job_events_scope);

    test_socket.init();
    jobs_socket.init();
    job_events_socket.init();

    test_scope.messages.push('Message Displayed Before Connection');

    test_socket.on('test', function(data) {
        test_scope.messages.push(data);
    });

    jobs_socket.on("status_changed", function(data) {
        jobs_scope.messages.push(data);
    });
}

SocketsController.$inject = [ '$scope', '$compile', 'ClearScope', 'Socket'];
