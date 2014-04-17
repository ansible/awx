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
        job_events_scope = $scope.$new();

    var test_socket = Socket({ scope: test_scope, endpoint: "test" }),
        jobs_socket = Socket({ scope: jobs_scope, endpoint: "jobs" }),
        job_events_socket = Socket({ scope: job_events_scope, endpoint: "job_events" });

    var test_element = angular.element(document.getElementById('test_url'));
    $compile(test_element)(test_scope);
    var jobs_element = angular.element(document.getElementById("jobs_url"));
    $compile(jobs_element)(jobs_scope);
    var job_events_element = angular.element(document.getElementById("job_events_url"));
    $compile(job_events_element)(job_events_scope);

    test_socket.init();
    jobs_socket.init();
    job_events_socket.init();

    test_scope.messages = ['Message Displayed Before Connection'];

    test_socket.on('test', function(data) {
            test_scope.messages.push(data);
    });
}

SocketsController.$inject = [ '$scope', '$compile', 'ClearScope', 'Socket'];
