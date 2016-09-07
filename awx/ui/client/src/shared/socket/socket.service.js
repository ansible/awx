/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import ReconnectingWebSocket from 'reconnectingwebsocket';
export default
['$rootScope', '$location', '$log', 'Authorization','$state',
    function ($rootScope, $location, $log, Authorization, $state) {
        return {
            init: function() {
                var self = this,
                    // token = Authorization.getToken(),
                    host = window.location.host,
                    url = "ws://" + host + "/websocket/";
                if (!$rootScope.sessionTimer || ($rootScope.sessionTimer && !$rootScope.sessionTimer.isExpired())) {
                    // We have a valid session token, so attempt socket connection
                    $log.debug('Socket connecting to: ' + url);
                    self.socket = new ReconnectingWebSocket(url, null, {
                        debug: true,
                        timeoutInterval: 3000,
                        maxReconnectAttempts: 10
                    });
                    self.socket.onopen = function () {
                        console.log('websocket connected'); //log errors
                        $rootScope.socketPromise.resolve();
                    };
                    //
                    // self.socket.onerror = function (error) {
                    //     console.log('Error Logged: ' + error); //log errors
                    // };
                    self.socket.onmessage = function (e) {
                        console.log('Received From Server: ' + e.data);
                        var data = JSON.parse(e.data);
                        // {'groups':
                        //      {'jobs': ['status_changed', 'summary'],
                        //       'schedules': ['changed'],
                        //       'ad_hoc_command_events': [ids,],
                        //       'job_events': [ids,],
                        //       'control': ['limit_reached'],
                        //      }
                        // }
                        if(data.group_name==="jobs"){

                            if (!('status' in data)){
                                // we know that this must have been a
                                // summary complete message
                                $log.debug('Job summary_complete ' + data.unified_job_id);
                                $rootScope.$emit('JobSummaryComplete', data);
                            }
                            if ($state.is('jobs')) {
                                $rootScope.$emit('JobStatusChange-jobs', data);
                            } else if ($state.includes('jobDetail') ||
                                $state.is('adHocJobStdout') ||
                                $state.is('inventorySyncStdout') ||
                                $state.is('managementJobStdout') ||
                                $state.is('scmUpdateStdout')) {

                                $log.debug("sending status to standard out");
                                $rootScope.$emit('JobStatusChange-jobStdout', data);
                            }
                            if ($state.includes('jobDetail')) {
                                $rootScope.$emit('JobStatusChange-jobDetails', data);
                            } else if ($state.is('dashboard')) {
                                $rootScope.$emit('JobStatusChange-home', data);
                            } else if ($state.is('portalMode')) {
                                $rootScope.$emit('JobStatusChange-portal', data);
                            } else if ($state.is('projects')) {
                                $rootScope.$emit('JobStatusChange-projects', data);
                            } else if ($state.is('inventoryManage')) {
                                $rootScope.$emit('JobStatusChange-inventory', data);
                            }
                        }
                        if(data.group_name==="job_events"){
                            $rootScope.$emit('job_events-'+data.job, data);
                        }
                        if(data.group_name==="schedules"){
                            $log.debug('Schedule  ' + data.unified_job_id + ' status changed to ' + data.status);
                            $rootScope.$emit('ScheduleStatusChange', data);
                        }
                        if(data.group_name==="ad_hoc_command_events"){
                            $rootScope.$emit('ad_hoc_command_events-'+data.ad_hoc_command, data);
                        }
                        if(data.group_name==="control"){
                            $log.debug(data.reason);
                            $rootScope.sessionTimer.expireSession('session_limit');
                            $state.go('signOut');
                        }

                        return self.socket;

                    };

                }
                else {
                    // encountered expired token, redirect to login page
                    $rootScope.sessionTimer.expireSession('idle');
                    $location.url('/login');
                }

                setTimeout(function() {
                        self.checkStatus();
                        $log.debug('socket status: ' + $rootScope.socketStatus);
                }, 2000);
            },
            subscribe2: function(state){
                console.log(state.name);
                this.emit(JSON.stringify(state.socket));
            },
            // subscribe: function(toState, toParams){
            //     if(toState.name === 'dashboard'){
            //         this.emit('{"groups":{"jobs": ["status_changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'jobDetail'){
            //         this.emit(`{"groups":{"jobs": ["status_changed", "summary"] , "job_events":[${toParams.id}]}}`);
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'jobStdout'){
            //         this.emit('{"groups":{"jobs": ["status_changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'jobs'){
            //         this.emit('{"groups":{"jobs": ["status_changed"] , "schedules": ["changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'portalMode'){
            //         this.emit('{"groups":{"jobs": ["status_changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'projects'){
            //         this.emit('{"groups":{"jobs": ["status_changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'inventoryManage'){
            //         this.emit('{"groups":{"jobs": ["status_changed"]}}');
            //         console.log(toState.name);
            //     }
            //     if(toState.name === 'adHocJobStdout'){
            //         this.emit(`{"groups":{"jobs": ["status_changed"] , "ad_hoc_command_events": [${toParams.id}]}}`);
            //         console.log(toState.name);
            //     }
            // },
            checkStatus: function() {

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
                // Check connection status
                var self = this;
                if(self){
                    if(self.socket){
                        if (self.socket.readyState === 0 ) {
                            $rootScope.socketStatus = 'connecting';
                        }
                        else if (self.socket.readyState === 1){
                            $rootScope.socketStatus = 'ok';
                        }
                        else if (self.socket.readyState === 2 || self.socket.readyState === 3 ){
                            $rootScope.socketStatus = 'error';
                        }
                        self.socketTip = getSocketTip(self.socketStatus);
                        return $rootScope.socketStatus;
                    }
                }

            },
            // on: function (eventName, callback) {
            //     var self = this;
            //     if(self){
            //       if(self.socket){
            //         // self.socket.onmessage(function (e) {
            //         //     var args = arguments;
            //         //     self.scope.$apply(function () {
            //         //         callback.apply(self.socket, args);
            //         //     });
            //         // });
            //       }
            //     }
            //
            // },
            emit: function (eventName, data, callback) {
                var self = this;
                $rootScope.socketPromise.promise.then(function(){
                    self.socket.send(eventName, data, function () {
                        var args = arguments;
                        self.scope.$apply(function () {
                            if (callback) {
                                callback.apply(self.socket, args);
                            }
                        });
                    });
                });
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
    }];
