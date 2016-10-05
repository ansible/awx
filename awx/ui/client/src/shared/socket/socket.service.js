/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import ReconnectingWebSocket from 'reconnectingwebsocket';
export default
['$rootScope', '$location', '$log','$state',
    function ($rootScope, $location, $log, $state) {
        var needsResubscribing = false;
        return {
            init: function() {
                var self = this,
                    host = window.location.host,
                    url = "ws://" + host + "/websocket/";
                if (!$rootScope.sessionTimer || ($rootScope.sessionTimer && !$rootScope.sessionTimer.isExpired())) {
                    // We have a valid session token, so attempt socket connection
                    $log.debug('Socket connecting to: ' + url);

                    self.socket = new ReconnectingWebSocket(url, null, {
                        timeoutInterval: 3000,
                        maxReconnectAttempts: 10
                    });

                    self.socket.onopen = function () {
                        $log.debug("Websocket connection opened.");
                        $rootScope.socketPromise.resolve();
                        self.checkStatus();
                        if(needsResubscribing){
                            self.subscribe(self.getLast());
                            needsResubscribing = false;
                        }

                    };

                    self.socket.onerror = function (error) {
                        self.checkStatus();
                        $log.debug('Websocket Error Logged: ' + error); //log errors
                    };

                    self.socket.onconnecting = function (event) {
                        self.checkStatus();
                        $log.debug('Websocket reconnecting');
                        needsResubscribing = true;
                    };

                    self.socket.onclose = function (event) {
                        self.checkStatus();
                        $log.debug(`Websocket disconnected`);
                    };

                    self.socket.onmessage = this.onMessage;

                    return self.socket;
                }
                else {
                    // encountered expired token, redirect to login page
                    $rootScope.sessionTimer.expireSession('idle');
                    $location.url('/login');
                }
            },
            onMessage: function(e){
                $log.debug('Received From Server: ' + e.data);
                var data = JSON.parse(e.data), str = "";
                if(data.group_name==="jobs" && !('status' in data)){
                    // we know that this must have been a
                    // summary complete message b/c status is missing
                    $log.debug('Job summary_complete ' + data.unified_job_id);
                    $rootScope.$emit('ws-jobs-summary', data);
                    return;
                }
                else if(data.group_name==="job_events"){
                    str = `ws-${data.group_name}-${data.job}`;
                }
                else if(data.group_name==="ad_hoc_command_events"){
                    str = `ws-${data.group_name}-${data.ad_hoc_command}`;
                }
                else if(data.group_name==="control"){
                    $log.debug(data.reason);
                    $rootScope.sessionTimer.expireSession('session_limit');
                    $state.go('signOut');
                }
                else {
                    // The naming scheme is "ws" then a
                    // dash (-) and the group_name.
                    // ex: 'ws-jobs'
                    str = `ws-${data.group_name}`;
                }
                $rootScope.$emit(str, data);
            },
            disconnect: function(){
                if(this.socket){
                    this.socket.close();
                }
            },
            subscribe: function(state){
                this.emit(JSON.stringify(state.socket));
                this.setLast(state);
            },
            unsubscribe: function(state){
                if(this.requiresNewSubscribe(state)){
                    this.emit(JSON.stringify(state.socket));
                }
                this.setLast(state);
            },
            setLast: function(state){
                this.last = state;
            },
            getLast: function(){
                return this.last;
            },
            requiresNewSubscribe(state){
                if (this.getLast() !== undefined){
                    if( _.isEmpty(state.socket.groups) && _.isEmpty(this.getLast().socket.groups)){
                        return false;
                    }
                    else {
                        return true;
                    }
                }
                else {
                    return true;
                }
            },
            checkStatus: function() {
                var self = this;
                if(self){
                    if(self.socket){
                        if (self.socket.readyState === 0 ) {
                            $rootScope.socketStatus = 'connecting';
                            $rootScope.socketTip = "Live events: attempting to connect to the Tower server.";
                        }
                        else if (self.socket.readyState === 1){
                            $rootScope.socketStatus = 'ok';
                            $rootScope.socketTip = "Live events: connected. Pages containing job status information will automatically update in real-time.";
                        }
                        else if (self.socket.readyState === 2 || self.socket.readyState === 3 ){
                            $rootScope.socketStatus = 'error';
                            $rootScope.socketTip = "Live events: error connecting to the Tower server.";
                        }
                        return;
                    }
                }

            },
            emit: function(data, callback) {
                var self = this;
                $log.debug('Sent to Websocket Server: ' + data);
                $rootScope.socketPromise.promise.then(function(){
                    self.socket.send(data, function () {
                        var args = arguments;
                        self.scope.$apply(function () {
                            if (callback) {
                                callback.apply(self.socket, args);
                            }
                        });
                    });
                });
            }
        };
    }];
