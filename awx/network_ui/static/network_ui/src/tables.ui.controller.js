
var util = require('./util.js');
var messages = require('./messages.js');
var ReconnectingWebSocket = require('reconnectingwebsocket');

var TablesUIController = function($scope, $window, $location) {

    $window.scope = $scope;
    $scope.disconnected = false;

    $scope.topology_id = $location.search().topology_id || 0;
    if (!$scope.disconnected) {
        $scope.control_socket = new ReconnectingWebSocket("ws://" + window.location.host + "/network_ui/tables?topology_id=" + $scope.topology_id,
                                                          null,
                                                          {debug: false, reconnectInterval: 300});
    } else {
        $scope.control_socket = {
            on_message: util.noop
        };
    }

    $scope.client_id = 0;
    $scope.message_id_seq = util.natural_numbers(0);

    $scope.onClientId = function(data) {
        $scope.client_id = data;
    };

    $scope.control_socket.onmessage = function(message) {
        var type_data = JSON.parse(message.data);
        var type = type_data[0];
        var data = type_data[1];
        $scope.handle_message(type, data);
        $scope.$apply();
    };

	$scope.control_socket.onopen = function() {
        //Ignore
	};

	// Call onopen directly if $scope.control_socket is already open
	if ($scope.control_socket.readyState === WebSocket.OPEN) {
		$scope.control_socket.onopen();
	}

    $scope.send_control_message = function (message) {
        var i = 0;
        message.sender = $scope.client_id;
        message.message_id = $scope.message_id_seq();
        if (message.constructor.name === "MultipleMessage") {
            for (i=0; i < message.messages.length; i++) {
                message.messages[i].message_id = $scope.message_id_seq();
            }
        }
        var data = messages.serialize(message);
        if (!$scope.disconnected) {
            $scope.control_socket.send(data);
            console.log("Sent message");
        } else {
            console.log(data);
        }
    };

    $scope.handle_message = function(msg_type, message) {

        var handler_name = 'on' + msg_type;
        if (typeof(this[handler_name]) !== "undefined") {
            this[handler_name](msg_type, message);
        } else {
            this.default_handler(msg_type, message);
        }
    };

    $scope.default_handler = function(msg_type, message) {
        console.log([msg_type, message]);
    };


    // End web socket
    //
    //


    $scope.onid = function(msg_type, message) {
        console.log(["Set client_id to" , message]);
        $scope.client_id = message;
    };

    $scope.ontopology_id = function(msg_type, message) {
        console.log(["Set topology_id to" , message]);
        $scope.topology_id = message;
        $location.search({topology_id: message});
    };

    $scope.onsheet = function(msg_type, message) {
        console.log("Update sheet");
        console.log(message);
        $scope.data = message.data;
        $scope.name = message.name;
        $scope.sheets.push(message.name);
        $scope.sheets_by_name[message.name] = message.data;
    };

    $scope.user = {
        name: 'world'
    };

    $scope.data = [];
    $scope.sheets = [];
    $scope.sheets_by_name = {};

    console.log("Tables UI started");

    $scope.$on('$destroy', function () {
        console.log("Tables UI stopping");
    });

    $scope.updateData = function (old_data, new_data, column_index, row_index, column_name, row_name) {
        console.log(['updateData', $scope.name, old_data, new_data, column_index, row_index, column_name, row_name]);
        $scope.send_control_message(new messages.TableCellEdit($scope.client_id,
                                                               $scope.name,
                                                               column_index,
                                                               row_index,
                                                               old_data,
                                                               new_data));
    };

    $scope.changeSheet = function(sheet) {
        $scope.name = sheet;
        $scope.data = $scope.sheets_by_name[sheet];
    };
};

exports.TablesUIController = TablesUIController;
console.log("Tables UI loaded");
