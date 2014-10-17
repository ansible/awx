/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Portal.js
 *
 *  Controller functions for portal mode
 *
 */


/**
 * @ngdoc function
 * @name controllers.function:Portal
 * @description This controller's for portal mode
*/
'use strict';

/**
 * @ngdoc method
 * @name controllers.function:Portal#Portal
 * @methodOf controllers.function:Portal
 * @description portal mode woohoo
 *
 *
*/
function PortalController($scope, $compile, $routeParams, $rootScope, $location, $log, Wait, ClearScope, Stream, Rest, GetBasePath, ProcessErrors,
    Button, PortalJobTemplate, GenerateList, JobTemplateList, SearchInit, PaginateInit, PlaybookRun){

        ClearScope('portal');

        var html,
        e,
        winHeight,
        available_height,
        list = JobTemplateList,
        view= GenerateList,
        defaultUrl = GetBasePath('job_templates'),
        buttons = {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()",
                ngShow:"socketStatus == 'error'"
            }
            // ,
            // stream: {
            //     ngClick: "showActivity()",
            //     awToolTip: "View Activity Stream",
            //     mode: 'all'
            // }
        };

        html = Button({
            btn: buttons.refresh,
            action: 'refresh',
            toolbar: true
        });

        // html += Button({
        //     btn: buttons.stream,
        //     action: 'stream',
        //     toolbar: true
        // });

        e = angular.element(document.getElementById('portal-list-actions'));
        e.html(html);
        $compile(e)($scope);

        if ($scope.removeLoadPortal) {
            $scope.removeLoadPortal();
        }
        $scope.removeLoadPortal = $scope.$on('LoadPortal', function () {
            winHeight = $(window).height();
            available_height = Math.floor(winHeight - $('#main-menu-container .navbar').outerHeight() - $('#refresh-row').outerHeight() - 30);
            $('.portal-container').height(available_height);

            view.inject( list, {
                id : 'portal-job-template',
                mode: 'edit',
                scope: $scope,
                breadCrumbs: false,
                searchSize: 'col-lg-6 col-md-6'
            });

            $rootScope.flashMessage = null;

            SearchInit({
                scope: $scope,
                set: 'job_templates',
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: defaultUrl
            });

            // Called from Inventories tab, host failed events link:
            if ($routeParams.name) {
                $scope[list.iterator + 'SearchField'] = 'name';
                $scope[list.iterator + 'SearchValue'] = $routeParams.name;
                $scope[list.iterator + 'SearchFieldLabel'] = list.fields.name.label;
            }

            $scope.search(list.iterator);

            PortalJobTemplate({
                scope: $scope,
                target: 'portal-jobs',
                // dashboard: data
            });

        });
        $scope.submitJob = function (id) {
            PlaybookRun({ scope: $scope, id: id });
        };

        $scope.refresh = function () {
            $scope.$emit('LoadPortal');
            // Wait('start');
            // loadedCount = 0;
            // Rest.setUrl(GetBasePath('dashboard'));
            // Rest.get()
            //     .success(function (data) {
            //         $scope.$emit('dashboardReady', data);
            //     })
            //     .error(function (data, status) {
            //         ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get dashboard: ' + status });
            //     });
        };

        $scope.refresh();

    }

PortalController.$inject = ['$scope', '$compile', '$routeParams', '$rootScope', '$location', '$log','Wait', 'ClearScope', 'Stream', 'Rest', 'GetBasePath', 'ProcessErrors',
    'Button', 'PortalJobTemplate', 'GenerateList' , 'JobTemplateList', 'SearchInit', 'PaginateInit', 'PlaybookRun'
];
