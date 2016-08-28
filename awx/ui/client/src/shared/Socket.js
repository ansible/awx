/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 *  @ngdoc function
 *  @name shared.function:Socket
 *  @description
 *  Socket.js
 *
 *  Wrapper for lib/socket.io-client/dist/socket.io.js.
 */

/* global io */


/**
 * @ngdoc method
 * @name shared.function:Socket#SocketIO
 * @methodOf shared.function:Socket
 * @description
 */
import ReconnectingWebSocket from 'reconnectingwebsocket'
export default
angular.module('SocketIO', ['Utilities'])

    .factory('Socket', ['$rootScope', '$location', '$log', 'Authorization', 'Store', function ($rootScope, $location, $log, Authorization, Store) {
        return function(params) {
            var scope = params.scope,
                host = window.location.host,
                endpoint = params.endpoint,
                protocol = $location.protocol(),
                config, socketPort,
                url;

            // Since some pages are opened in a new tab, we might get here before AnsibleConfig is available.
            // In that case, load from local storage.
            if ($AnsibleConfig) {
                socketPort = $AnsibleConfig.websocket_port;
            }
            else {
                $log.debug('getting web socket port from local storage');
                config = Store('AnsibleConfig');
                socketPort = config.websocket_port;
            }

            url = "ws://" + host + "/websocket/";
            // url = protocol + '://' + host + ':' + socketPort + '/socket.io/' + endpoint;
            $log.debug('opening socket connection to: ' + url);

            function getSocketTip(status) {
                var result = '';
                switch(status) {
                    case 'error':
                        result = "Live events: error connecting to the Tower server.";
                        break;
                    case 'connecting':
                        result = "Live events: attempting to connect to the Tower server.";
                        break;
                    case "ok":
                        result = "Live events: connected. Pages containing job status information will automatically update in real-time.";
                }
                return result;
            }

            return {
                scope: scope,
                url:  url,
                socket: null,

                init: function() {
                    var self = this,
                        token = Authorization.getToken();
                    if (!$rootScope.sessionTimer || ($rootScope.sessionTimer && !$rootScope.sessionTimer.isExpired())) {
                        // We have a valid session token, so attempt socket connection
                        $log.debug('Socket connecting to: ' + url);
                        self.scope.socket_url = url;
                        self.socket = new ReconnectingWebSocket(url, null, {
                            debug: true,
                            timeoutInterval: 3000,
                            maxReconnectAttempts: 10
                        });
                    }
                    else {
                        // encountered expired token, redirect to login page
                        $rootScope.sessionTimer.expireSession('idle');
                        $location.url('/login');
                    }
                },
                checkStatus: function() {
                    // Check connection status
                    var self = this;
                    if(self){
                        if(self.socket){
                            if (self.socket.readyState === 0 ) {
                                self.scope.socketStatus = 'connecting';
                            }
                            else if (self.socket.readyState === 1){
                                self.scope.socketStatus = 'ok';
                            }
                            else if (self.socket.readyState === 2 || self.socket.readyState === 3 ){
                                self.scope.socketStatus = 'error';
                            }
                            self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            return self.scope.socketStatus;
                        }
                    }

                },
                on: function (eventName, callback) {
                    var self = this;
                    if(self){
                      if(self.socket){
                        self.socket.onmessage(eventName, function (e) {
                            console.log('Received From Server: ' + e.data);
                            var args = arguments;
                            self.scope.$apply(function () {
                                callback.apply(self.socket, args);
                            });
                        });
                      }
                    }

                },
                emit: function (eventName, data, callback) {
                    var self = this;
                    self.socket.send(eventName, data, function () {
                        var args = arguments;
                        self.scope.$apply(function () {
                            if (callback) {
                                callback.apply(self.socket, args);
                            }
                        });
                    });
                },
                getUrl: function() {
                    return url;
                },
                removeAllListeners: function (eventName) {
                    var self = this;
                    if(self){
                      if(self.socket){
                        self.socket.removeEventListener(eventName);
                      }
                    }
                },
            };
        };
    }]);
