/**********************************************
 * sampleApp.js
 *
 * Copyright (c) 2013-2014 Ansible, Inc.
 *
 */

'use strict';

angular.module('sampleApp', ['ngRoute', 'AngularScheduler', 'Timezones'])
        
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider
        .when('/', {
            templateUrl: 'partials/main.html',
            controller: 'sampleController'
        })
        .otherwise({
            redirectTo: '/'
        });
    }])

    .constant('AngularScheduler.partial', '/lib/angular-scheduler.html')
    .constant('AngularScheduler.useTimezone', false)
    .constant('AngularScheduler.showUTCField', false)
    .constant('$timezones.definitions.location', '/bower_components/angular-tz-extensions/tz/data')

    .controller('sampleController', ['$scope', '$filter', 'SchedulerInit', function($scope, $filter, SchedulerInit) {
    
        var scheduler = SchedulerInit({ scope: $scope });
       
        scheduler.inject('form-container', true);

        console.log('User timezone: ');
        console.log(scheduler.getUserTimezone());

        $scope.setRRule = function() {
            $scope.inputRRuleMsg = '';
            $scope.inputRRuleMsg = scheduler.setRRule($scope.inputRRule);
        };
        
        $scope.resetForm = function() { scheduler.clear(); };

        $scope.saveForm = function() {
            if (scheduler.isValid()) {
                var schedule = scheduler.getValue(),
                    html =
                    "<form>\n" +
                    "<div class=\"form-group\">\n" +
                    "<label>RRule</label>\n" +
                    "<textarea id=\"rrule-result\" readonly class=\"form-control\" rows=\"8\">" + schedule.rrule + "</textarea>\n" +
                    "</div>\n" +
                    "</form>\n",
                    wheight = $(window).height(),
                    wwidth = $(window).width(),
                    w, h;
                
                w = (600 > wwidth) ? wwidth : 600;
                h = (400 > wheight) ? wheight : 400;

                $('#message').html(html)
                    .dialog({
                        title: schedule.name,
                        modal: true,
                        width: w,
                        height: h,
                        position: 'center',
                        buttons: { OK: function() { $(this).dialog('close');} },
                        open: function () {
                            // fix the close button
                            $('.ui-dialog[aria-describedby="message"]').find('.ui-dialog-titlebar button')
                                .empty().attr({ 'class': 'close' }).text('x');
                            // fix the OK button
                            $('.ui-dialog[aria-describedby="message"]').find('.ui-dialog-buttonset button:first')
                                .attr({ 'class': 'btn btn-primary', 'id': 'modal-ok-button' });
                        }
                    });
            }
        };

    }]);
