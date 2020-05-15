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
    ['$rootScope', '$cookies', 'CreateDialog', 'Authorization',
        'Store', '$interval', '$state', '$q', 'i18n',
    function ($rootScope, $cookies, CreateDialog, Authorization,
        Store, $interval, $state, $q, i18n) {
        return {

            sessionTime: null,
            timeout: null,

            getSessionTime: function () {
                if(Store('sessionTime') && Store('sessionTime')[$rootScope.current_user.id]){
                    return Store('sessionTime')[$rootScope.current_user.id].time;
                }
                else {
                    return 0;
                }
            },

            isExpired: function (increase) {
                var stime = this.getSessionTime(),
                    now = new Date().getTime();
                if ((stime - now) <= 0) {
                    //expired
                    return true;
                }
                else if(increase){
                    return false;
                }
                else{
                    // not expired. move timer forward.
                    this.moveForward();
                    return false;
                }
            },

            isIdle: function() {
                var stime = this.getSessionTime()/1000,
                    now = new Date().getTime()/1000,
                    diff = stime-now;

                if(diff < 60){
                    return diff;
                }
                else {
                    return false;
                }
            },

            expireSession: function (reason) {
                if(reason === 'session_limit'){
                    $rootScope.sessionLimitExpired = true;
                    $rootScope.sessionExpired = false;
                }
                else if(reason === 'idle'){
                    $rootScope.sessionExpired = true;
                    $rootScope.sessionLimitExpired = false;
                }
                this.sessionTime = 0;
                this.clearTimers();
                $cookies.put('sessionExpired', true);
            },

            moveForward: function () {
                var tm, t, x, y;
                tm = ($AnsibleConfig.session_timeout) ? $AnsibleConfig.session_timeout : 1800;
                t = new Date().getTime() + (tm * 1000);
                x = {
                        time: t,
                        loggedIn: true
                };
                if(Store('sessionTime')){
                    y = Store('sessionTime');
                }
                else {
                    y = {};
                }
                y[$rootScope.current_user.id] = x;
                Store('sessionTime' , y);
                $rootScope.sessionExpired = false;
                $cookies.put('sessionExpired', false);
                this.startTimers();
            },

            startTimers: function(){
                var that = this;
                this.clearTimers();
                $rootScope.expireTimer = $interval(function() {
                    var idle = that.isIdle();
                    if (that.isExpired(true)) {
                        if($('#idle-modal').is(':visible')){
                            if($('#idle-modal').dialog('isOpen')){
                                $('#idle-modal').dialog('close');
                            }
                        }
                        that.expireSession('idle');
                        $state.go('signOut');
                        return;
                    }
                    if(Store('sessionTime') &&
                        Store('sessionTime')[$rootScope.current_user.id] &&
                        Store('sessionTime')[$rootScope.current_user.id].loggedIn === false){
                            that.expireSession();
                            $state.go('signOut');
                            return;
                    }
                    if(idle !== false){
                        if($('#idle-modal').is(':visible')){
                            $('#remaining_seconds').html(Math.round(idle));
                        }
                        else {
                            var buttons = [{
                                "label": i18n._("Continue"),
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
                                title: i18n._("Idle Session"),
                                scope: $rootScope,
                                buttons: buttons,
                                dialogClass: "no-close",
                                width: 470,
                                height: 240,
                                minWidth: 200,
                                callback: 'IdleDialogReady'
                            });
                        }
                    }
                    else if(!idle){
                        if($('#idle-modal').is(':visible')){
                            $('#idle-modal').dialog('close');
                        }
                    }


                }, 1000);

            },

            clearTimers: function(){
                $interval.cancel($rootScope.expireTimer);
                delete $rootScope.expireTimer;
            },

            init: function () {
                var deferred = $q.defer();
                this.moveForward();
                deferred.resolve(this);
                return deferred.promise;

            }
        };
    }
];
