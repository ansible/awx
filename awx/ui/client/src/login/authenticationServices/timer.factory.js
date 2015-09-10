/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 *  @ngdoc function
 *  @name shared.function:Timer
 *  @description
 *  Timer.js
 *
 *  Use to track user idle time and expire session. Timeout
 *  duration set in config.js
 *
 */

/**
 * @ngdoc method
 * @name shared.function:Timer#TimerService
 * @methodOf shared.function:Timer
 * @description
 */
export default
    ['$rootScope', '$cookieStore', 'transitionTo', 'CreateDialog', 'Authorization',
    function ($rootScope, $cookieStore, transitionTo, CreateDialog, Authorization) {
        return {

            sessionTime: null,
            timeout: null,

            getSessionTime: function () {
                return (this.sessionTime) ? this.sessionTime : $cookieStore.get('sessionTime');
            },

            isExpired: function () {
                var stime = this.getSessionTime(),
                    now = new Date().getTime();
                if ((stime - now) <= 0) {
                    //expired
                    return true;
                } else {
                    // not expired. move timer forward.
                    this.moveForward();
                    return false;
                }
            },

            isIdle: function() {
                var stime = this.getSessionTime()/1000,
                    now = new Date().getTime()/1000,
                    diff = stime-now;

                if(diff < 61){
                    return true;
                }
                else {
                    return false;
                }
            },

            expireSession: function () {
                this.sessionTime = 0;
                $rootScope.sessionExpired = true;
                this.clearTimers();
                $cookieStore.put('sessionExpired', true);
                transitionTo('signOut');
            },

            moveForward: function () {
                var tm, t;
                tm = ($AnsibleConfig) ? $AnsibleConfig.session_timeout : 1800;
                t = new Date().getTime() + (tm * 1000);
                this.sessionTime = t;
                $cookieStore.put('sessionTime', t);
                $rootScope.sessionExpired = false;
                $cookieStore.put('sessionExpired', false);

                this.startTimers();
            },

            startTimers: function() {
                var that = this,
                tm = ($AnsibleConfig) ? $AnsibleConfig.session_timeout : 1800,
                t = tm - 60;

                this.clearTimers();

                // make a timeout that will go off in 30 mins to log them out
                // unless they extend their time
                $rootScope.endTimer = setTimeout(function(){
                    that.expireSession();
                }, tm * 1000);

                // notify the user a minute before the end of their session that
                // their session is about to expire
                if($rootScope.idleTimer){
                    clearTimeout($rootScope.idleTimer);
                }
                $rootScope.idleTimer = setTimeout(function() {
                    if(that.isIdle() === true){
                        var buttons = [{
                          "label": "Continue",
                          "onClick": function() {
                              // make a rest call here to force the API to
                              // move the session time forward
                              Authorization.getUser();
                              that.moveForward();
                              $(this).dialog('close');

                          },
                          "class": "btn btn-primary",
                          "id": "idle-modal-button"
                        }];

                        if ($rootScope.removeIdleDialogReady) {
                            $rootScope.removeIdleDialogReady();
                        }
                        $rootScope.removeIdleDialogReady = $rootScope.$on('IdleDialogReady', function() {
                            $('#idle-modal').show();
                            $('#idle-modal').dialog('open');
                        });
                        CreateDialog({
                            id: 'idle-modal'    ,
                            title: "Idle Session",
                            scope: $rootScope,
                            buttons: buttons,
                            width: 470,
                            height: 240,
                            minWidth: 200,
                            callback: 'IdleDialogReady'
                        });
                    }
                }, t * 1000);


            },

            clearTimers: function(){
                clearTimeout($rootScope.idleTimer);
                clearTimeout($rootScope.endTimer);
            },

            init: function () {
                this.moveForward();
                return this;
            }
        };
    }
];
