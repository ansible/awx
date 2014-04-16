/**************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Socket.js
 *
 *  Wrapper for lib/socket.io-client/dist/socket.io.js.
 */

/* global io */

'use strict';

angular.module('SocketIO', ['AuthService', 'Utilities'])

    .factory('Socket', ['$rootScope', '$location', '$log', 'Authorization', 'Alert', function ($rootScope, $location, $log, Authorization, Alert) {
        return function(params) {
            var scope = params.scope,
                host = $location.host(),
                protocol = $location.protocol(),
                url = protocol + '://' + host + ':8080';

            if (scope.removeSocketErrorEncountered) {
                scope.removeSocketErrorEncountered();
            }
            scope.removeSocketErrorEncountered = scope.$on('SocketErrorEncountered', function(e, reason) {
                if (reason === 'Session expired') {
                    // encountered expired token, ask user to log in again
                    $rootScope.sessionTimer.expireSession();
                    $location.url('/login');
                }
                else {
                    Alert("Socket Error", "Attempt to refresh page failed with: " + reason, "alert-danger");
                    // should we do something more here?
                }
            });

            return {
                scope: scope,
                url:  url,
                socket: null,
                init: function() {
                    var self = this,
                        token = Authorization.getToken();
                    if (!$rootScope.sessionTimer.isExpired()) {
                        // We have a valid session token, so attmempt socket connection
                        $log.debug('Socket connecting to: ' + url);
                        self.scope.socket_url = url;
                        self.socket = io.connect(url, { headers:
                            {
                                'Authorization': 'Token ' + token,
                                "X-Auth-Token": 'Token ' + token
                            },
                            'connect timeout': 3000,
                            'try multiple transports': false,
                            'max reconneciton attemps': 3,
                            'reconnection limit': 3000,

                        });
                        self.socket.on('connection', function() {
                            $log.debug('Socket connecting...');
                            self.scope.socket_status = 'connecting';
                        });
                        self.socket.on('connect', function() {
                            $log.debug('Socket connection established');
                            self.scope.socket_status = 'ok';
                        });
                        self.socket.on('connect_failed', function(reason) {
                            var r = reason || 'connection refused by host';
                            $log.error('Socket connection failed: ' + r);
                            self.scope.socket_status = 'error';
                            self.scope.socket_reason = r;
                            self.scope.$emit('SocketErrorEncountered', 'Connection failed: ' + r);
                        });
                        self.socket.on('diconnect', function() {
                            $log.debug('Socket disconnected');
                            self.scope.socket_status = 'disconnected';
                        });
                        self.socket.on('error', function(reason) {
                            var r = reason || 'connection refused by host';
                            $log.error('Socket error encountered: ' + r);
                            self.scope.socket_status = 'error';
                            self.scope.socket_reason = r;
                            self.scope.$emit('SocketErrorEncountered', r);
                        });
                        self.socket.on('reconnecting', function() {
                            $log.debug('Socket attempting reconnect...');
                            self.scope.socket_status = 'connecting';
                        });
                        self.socket.on('reconnect', function() {
                            $log.debug('Socket reconnected');
                            self.scope.socket_status = 'ok';
                        });
                        self.socket.on('reconnect_failed', function(reason) {
                            $log.error('Socket reconnect failed: ' + reason);
                            self.scope.socket_status = 'error';
                            self.scope.socket_reason = reason;
                            self.scope.$emit('SocketErrorEncountered', 'Connection failed: ' + reason);
                        });
                    }
                    else {
                        // Encountered expired token
                        self.scope.$emit('SocketErrorEncountered', 'Session expired');
                    }
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
                }
            };
        };
    }]);
