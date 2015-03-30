/**************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
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
angular.module('TimerService', ['ngCookies', 'Utilities'])
    .factory('Timer', ['$rootScope', '$cookieStore', '$location', 'GetBasePath', 'Empty',
        function ($rootScope, $cookieStore) {
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

                expireSession: function () {
                    this.sessionTime = 0;
                    $rootScope.sessionExpired = true;
                    $cookieStore.put('sessionExpired', true);
                },

                moveForward: function () {
                    var tm, t;
                    tm = ($AnsibleConfig) ? $AnsibleConfig.session_timeout : 1800;
                    t = new Date().getTime() + (tm * 1000);
                    this.sessionTime = t;
                    $cookieStore.put('sessionTime', t);
                    $rootScope.sessionExpired = false;
                    $cookieStore.put('sessionExpired', false);
                },

                init: function () {
                    this.moveForward();
                    return this;
                }
            };
        }
    ]);
