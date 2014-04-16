/************************************
* Copyright (c) 2014 AnsibleWorks, Inc.
*
*  Sockets.js
*  SocketsController- simple test of socket connection
*
*/

'use strict';

function SocketsController ($scope, ClearScope, Socket) {

    ClearScope();

    var socket = Socket({ scope: $scope });
    socket.init(); //make the connection

    $scope.messages = ['Stuff happened', 'message received', 'blah blah bob blah'];

    socket.on('anything', function(data) {
        $scope.messages.push(data);
    });

}

SocketsController.$inject = [ '$scope', 'ClearScope', 'Socket'];
