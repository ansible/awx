/**************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name lib.ansible.function:Socket
 *  @description
 *  Socket.js
 *
 *  Wrapper for lib/socket.io-client/dist/socket.io.js.
 */

/* global io */


/**
 * @ngdoc method
 * @name lib.ansible.function:Socket#SocketIO
 * @methodOf lib.ansible.function:Socket
 * @description
 */
angular.module('SocketIO', ['AuthService', 'Utilities'])

    .factory('Socket', ['$rootScope', '$location', '$log', 'Authorization', 'Store', function ($rootScope, $location, $log, Authorization, Store) {
        return function(params) {
            var scope = params.scope,
                host = $location.host(),
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
            url = protocol + '://' + host + ':' + socketPort + '/socket.io/' + endpoint;
            $log.debug('opening socket connection to: ' + url);

            function getSocketTip(status) {
                var result = '';
                switch(status) {
                    case 'error':
                        result = "Live events: error connecting to the Tower server. Click for troubleshooting help.";
                        break;
                    case 'connecting':
                        result = "Live events: attempting to connect to the Tower server. Click for troubleshooting help.";
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
                        self.socket = io.connect(url, {
                            query: "Token="+token,
                            headers:
                            {
                                'Authorization': 'Token ' + token,      // i don't think these are actually inserted into the header--jt
                                'X-Auth-Token': 'Token ' + token
                            },
                            'connect timeout': 3000,
                            'try multiple transports': false,
                            'max reconnection attempts': 3,
                            'reconnection limit': 3000
                        });

                        self.socket.on('connection', function() {
                            $log.debug('Socket connecting...');
                            self.scope.$apply(function () {
                                self.scope.socketStatus = 'connecting';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('connect', function() {
                            $log.debug('Socket connection established');
                            self.scope.$apply(function () {
                                self.scope.socketStatus = 'ok';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('connect_failed', function(reason) {
                            var r = reason || 'connection refused by host';
                            $log.error('Socket connection failed: ' + r);
                            self.scope.$apply(function () {
                                self.scope.socketStatus = 'error';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });

                        });
                        self.socket.on('diconnect', function() {
                            $log.debug('Socket disconnected');
                            self.scope.$apply(function() {
                                self.socketStatus = 'error';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('error', function(reason) {
                            var r = reason || 'connection refused by host';
                            $log.debug('Socket error: ' + r);
                            $log.error('Socket error: ' + r);
                            self.scope.$apply(function() {
                                self.scope.socketStatus = 'error';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('reconnecting', function() {
                            $log.debug('Socket attempting reconnect...');
                            self.scope.$apply(function() {
                                self.scope.socketStatus = 'connecting';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('reconnect', function() {
                            $log.debug('Socket reconnected');
                            self.scope.$apply(function() {
                                self.scope.socketStatus = 'ok';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                        self.socket.on('reconnect_failed', function(reason) {
                            $log.error('Socket reconnect failed: ' + reason);
                            self.scope.$apply(function() {
                                self.scope.socketStatus = 'error';
                                self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                            });
                        });
                    }
                    else {
                        // encountered expired token, redirect to login page
                        $rootScope.sessionTimer.expireSession();
                        $location.url('/login');
                    }
                },
                checkStatus: function() {
                    // Check connection status
                    var self = this;
                    if (self.socket.socket.connected) {
                        self.scope.socketStatus = 'ok';
                    }
                    else if (self.socket.socket.connecting || self.socket.socket.reconnecting) {
                        self.scope.socketStatus = 'connecting';
                    }
                    else {
                        self.scope.socketStatus = 'error';
                    }
                    self.scope.socketTip = getSocketTip(self.scope.socketStatus);
                    return self.scope.socketStatus;
                },
                on: function (eventName, callback) {
                    var self = this;
                    self.socket.on(eventName, function () {
                        var args = arguments;
                        self.scope.$apply(function () {
                            callback.apply(self.socket, args);
                        });
                    });
                },
                emit: function (eventName, data, callback) {
                    var self = this;
                    self.socket.emit(eventName, data, function () {
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
                }
            };
        };
    }]);
