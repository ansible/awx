// /************************************
//  * Copyright (c) 2014 AnsibleWorks, Inc.
//  *
//  *
//  *  Portal.js
//  *
//  *  Controller functions for portal mode
//  *
//  */


// /**
//  * @ngdoc function
//  * @name controllers.function:Portal
//  * @description This controller's for portal mode
// */
// 'use strict';

// /**
//  * @ngdoc method
//  * @name controllers.function:Portal#Portal
//  * @methodOf controllers.function:Portal
//  * @description portal mode woohoo
//  *
//  *
// */
// function Portal($scope, $compile, $routeParams, $rootScope, $location, $log, Wait,
//     ClearScope, Stream, Rest, GetBasePath, ProcessErrors, Button){

//     ClearScope('portal');

//     // var buttons, html, e, waitCount, loadedCount,borderStyles, jobs_scope, schedule_scope;

//     // // Add buttons to the top of the Home page. We're using lib/ansible/generator_helpers.js-> Buttons()
//     // // to build buttons dynamically and insure all styling and icons match the rest of the application.
//     // buttons = {
//     //     refresh: {
//     //         mode: 'all',
//     //         awToolTip: "Refresh the page",
//     //         ngClick: "refresh()",
//     //         ngShow:"socketStatus == 'error'"
//     //     },
//     //     stream: {
//     //         ngClick: "showActivity()",
//     //         awToolTip: "View Activity Stream",
//     //         mode: 'all'
//     //     }
//     // };

//     // html = Button({
//     //     btn: buttons.refresh,
//     //     action: 'refresh',
//     //     toolbar: true
//     // });

//     // html += Button({
//     //     btn: buttons.stream,
//     //     action: 'stream',
//     //     toolbar: true
//     // });

//     // e = angular.element(document.getElementById('home-list-actions'));
//     // e.html(html);
//     // $compile(e)($scope);

//     // waitCount = 4;
//     // loadedCount = 0;

//     // if (!$routeParams.login) {
//     //     // If we're not logging in, start the Wait widget. Otherwise, it's already running.
//     //     //Wait('start');
//     // }

//     // if ($scope.removeWidgetLoaded) {
//     //     $scope.removeWidgetLoaded();
//     // }
//     // $scope.removeWidgetLoaded = $scope.$on('WidgetLoaded', function (e, label, jobscope, schedulescope) {
//     //     // Once all the widgets report back 'loaded', turn off Wait widget
//     //     if(label==="dashboard_jobs"){
//     //         jobs_scope = jobscope;
//     //         schedule_scope = schedulescope;
//     //     }
//     //     loadedCount++;
//     //     if (loadedCount === waitCount) {
//     //         $(window).resize(_.debounce(function() {
//     //             $scope.$emit('ResizeJobGraph');
//     //             $scope.$emit('ResizeHostGraph');
//     //             $scope.$emit('ResizeHostPieGraph');
//     //             Wait('stop');
//     //         }, 500));
//     //         $(window).resize();
//     //     }
//     // });

//     // if ($scope.removeDashboardReady) {
//     //     $scope.removeDashboardReady();
//     // }
//     // $scope.removeDashboardReady = $scope.$on('dashboardReady', function (e, data) {
//     //     nv.dev=false;


//     //     borderStyles = {"border": "1px solid #A9A9A9",
//     //         "border-radius": "4px",
//     //         "padding": "5px",
//     //         "margin-bottom": "15px"};
//     //     $('.graph-container').css(borderStyles);

//     //     var winHeight = $(window).height(),
//     //     available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
//     //     $('.graph-container').height(available_height/2);
//     //     // // chart.update();

//     //     DashboardCounts({
//     //         scope: $scope,
//     //         target: 'dash-counts',
//     //         dashboard: data
//     //     });

//     //     JobStatusGraph({
//     //         scope: $scope,
//     //         target: 'dash-job-status-graph',
//     //         dashboard: data
//     //     });

//     //     if ($rootScope.user_is_superuser === true) {
//     //         waitCount = 5;
//     //         HostGraph({
//     //             scope: $scope,
//     //             target: 'dash-host-count-graph',
//     //             dashboard: data
//     //         });
//     //     }
//     //     else{
//     //         $('#dash-host-count-graph').remove(); //replaceWith("<div id='dash-host-count-graph' class='left-side col-sm-12 col-xs-12'></div>");
//     //     }
//     //     DashboardJobs({
//     //         scope: $scope,
//     //         target: 'dash-jobs-list',
//     //         dashboard: data
//     //     });
//     //     HostPieChart({
//     //         scope: $scope,
//     //         target: 'dash-host-status-graph',
//     //         dashboard: data
//     //     });

//     // });

//     // if ($rootScope.removeJobStatusChange) {
//     //     $rootScope.removeJobStatusChange();
//     // }
//     // $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function() {
//     //     jobs_scope.refreshJobs();
//     //     $scope.$emit('ReloadJobStatusGraph');

//     // });

//     // if ($rootScope.removeScheduleChange) {
//     //     $rootScope.removeScheduleChange();
//     // }
//     // $rootScope.removeScheduleChange = $rootScope.$on('ScheduleChange', function() {
//     //     schedule_scope.refreshSchedules();
//     //     $scope.$emit('ReloadJobStatusGraph');
//     // });

//     // $scope.showActivity = function () {
//     //     Stream({
//     //         scope: $scope
//     //     });
//     // };

//     // $scope.refresh = function () {
//     //     Wait('start');
//     //     loadedCount = 0;
//     //     Rest.setUrl(GetBasePath('dashboard'));
//     //     Rest.get()
//     //         .success(function (data) {
//     //             $scope.$emit('dashboardReady', data);
//     //         })
//     //         .error(function (data, status) {
//     //             ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get dashboard: ' + status });
//     //         });
//     // };

//     // $scope.refresh();

// }

// Home.$inject = ['$scope', '$compile', '$routeParams', '$rootScope', '$location', '$log','Wait',
//     'ClearScope', 'Stream', 'Rest', 'GetBasePath', 'ProcessErrors', 'Button'
// ];
