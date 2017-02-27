/* jshint ignore:start */

/*
*       pendo.io Angular Module
*
*       (c) 2013 pendo.io
*/



(function(angular) {

    'use strict';

    var ap = {};
    ap.waitForPendo = function(delay, registerFn) {
        var waitFn = function() { ap.waitForPendo( delay, registerFn); };

        if (ap.disabled) {
            ap.afterReenable = waitFn;
            return;
        }

        if(window.hasOwnProperty('pendo') && window.pendo.initialize) {
            registerFn(pendo);
        } else {
            setTimeout(waitFn, delay);
        }
    };

    angular.module('pendolytics', [])
    .provider('$pendolytics', function() {

        var eventCache = [];
        var service = {};

        var serviceImpl = {
            pageLoad: function() {
                eventCache.push( {method: 'pageLoad', args: [] });
            },
            identify: function( newName, accountId, props ) {
                var saveMe = { method: 'identify', args: [ newName, accountId, props ] };
                eventCache.push(saveMe);
            },
            updateOptions: function( obj ) {
                eventCache.push({ method: 'updateOptions', args: [obj]});
            },

            /*
             * This will allow for initalizing the Agent asynchronously
             * with an API key that is set after the agent has been set.
             */
            initialize: function(options) {
                eventCache.unshift({
                    method: 'initialize',
                    args: [options]
                });
            }
        };

        service.pageLoad = function() {
            serviceImpl.pageLoad();
        };

        service.load = function() {
            pendo.log("PENDO LOADED!!!");

            serviceImpl = pendo;

            // Flush the cache
            angular.forEach(eventCache, function(item) {
                pendo[item.method].apply(pendo, item.args);
            });

        };

        service.identify = function(newName, accountId, props){
            serviceImpl.identify(newName, accountId, props);
        };

        service.updateOptions = function(json_obj) {
            serviceImpl.updateOptions(json_obj);
        };

        service.initialize = function(options){
            serviceImpl.initialize(options);
        };

        service.enable = function(){
            if (ap.disabled) {
                ap.disabled = false;
                ap.afterReenable();
            }
        };

        service.disable = function(){
            ap.disabled = true;
        };

        service.bootstrap = function() {
            if (!service.bootstrapped) {
                var script = document.createElement('script');
                script.type = 'text/javascript';
                script.async = true;
                script.src = ('https:' === document.location.protocol ? 'https://' : 'http://' ) + 'd3accju1t3mngt.cloudfront.net/js/pa.min.js';
                var firstScript = document.getElementsByTagName('script')[0];
                firstScript.parentNode.insertBefore(script, firstScript);
                service.bootstrapped = true;
            }
        };

        return {
            $get: function(){ return service; },
            doNotAutoStart: function() {
                service.doNotAutoStart = true;
            }
        };

    }).run(['$rootScope', '$pendolytics', function($rootScope, $pendolytics) {
        if (!$pendolytics.doNotAutoStart) {
            $pendolytics.bootstrap();
        }
        ap.waitForPendo( 500, function( p ) {
            $pendolytics.load();
            $rootScope.$on('$locationChangeSuccess', function() {
                $pendolytics.pageLoad();
            });
        });
    }]);

})(angular);
