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

    .run(['$rootScope', function($rootScope) {
        $rootScope.toggleTab = function(e, tab, tabs) {
            e.preventDefault();
            $('#' + tabs + ' #' + tab).tab('show');
        };
    }])

    .constant('AngularScheduler.partial', '/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', '/bower_components/angular-tz-extensions/tz/data')

    .controller('sampleController', ['$scope', '$filter', 'SchedulerInit', function($scope, $filter, SchedulerInit) {
    
        var scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });
       
        scheduler.inject('form-container', true);
        scheduler.injectDetail('details-tab', true);

        $('#scheduler-tabs a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
            // Only show detail tab if schedule is valid
            if ($(e.target).text() === 'Details') {
                if (!scheduler.isValid()) {
                    $('#scheduler-link').tab('show');
                }
            }
        });

        $scope.setRRule = function() {
            $scope.inputRRuleMsg = '';
            $scope.inputRRuleMsg = scheduler.setRRule($scope.inputRRule);
        };
        
        $scope.resetForm = function() { scheduler.clear(); };

        $scope.saveForm = function() {
            if (scheduler.isValid()) {
                var schedule = scheduler.getValue(),
                    wheight = $(window).height(),
                    wwidth = $(window).width(),
                    w, h;

                $('#message').empty();
                scheduler.injectDetail('message', true);

                w = (600 > wwidth) ? wwidth : 600;
                h = (635 > wheight) ? wheight : 635;

                $('#message').dialog({
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
