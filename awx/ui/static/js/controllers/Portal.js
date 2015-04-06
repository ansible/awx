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


/**
 * @ngdoc method
 * @name controllers.function:Portal#Portal
 * @methodOf controllers.function:Portal
 * @description portal mode woohoo
 *
 *
*/
export function PortalController($scope, $compile, $routeParams, $rootScope, $location, $log, Wait, ClearScope, Stream, Rest, GetBasePath, ProcessErrors,
    PortalJobsWidget, GenerateList, PortalJobTemplateList, SearchInit, PaginateInit, PlaybookRun){

        ClearScope('portal');

        var jobs_scope,
        list = PortalJobTemplateList,
        view= GenerateList,
        defaultUrl = GetBasePath('job_templates'),
        max_rows;

        if ($scope.removeLoadPortal) {
            $scope.removeLoadPortal();
        }
        $scope.removeLoadPortal = $scope.$on('LoadPortal', function () {

            view.inject( list, {
                id : 'portal-job-templates',
                mode: 'edit',
                scope: $scope,
                breadCrumbs: false,
                searchSize: 'col-lg-6 col-md-6'
            });

            $scope.job_templatePageSize = $scope.getMaxRows();

            SearchInit({
                scope: $scope,
                set: 'job_templates',
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: defaultUrl,
                pageSize: $scope.job_templatePageSize
            });

            $scope.search(list.iterator);

            PortalJobsWidget({
                scope: $scope,
                target: 'portal-jobs',
                searchSize: 'col-lg-6 col-md-6'
            });
        });
        if ($scope.removeWidgetLoaded) {
            $scope.removeWidgetLoaded();
        }
        $scope.removeWidgetLoaded = $scope.$on('WidgetLoaded', function (e, label, jobscope) {
            if(label==="portal_jobs"){
                jobs_scope = jobscope;
            }
            $('.actions-column:eq(0)').text('Launch');
            $('.actions-column:eq(1)').text('Details');
            $('.list-well:eq(1)').css('margin-top' , '0px');
        });

        if ($rootScope.removeJobStatusChange) {
            $rootScope.removeJobStatusChange();
        }
        $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function() {
            jobs_scope.search('portal_job'); //processEvent(event);
        });

        $scope.getMaxRows = function(){
            var docw = $(window).width(),
                box_height, available_height, search_row, page_row, height, header, row_height;

            available_height = Math.floor($(window).height() - $('#main-menu-container .navbar').outerHeight() - $('#refresh-row').outerHeight() - 35);
            $('.portal-job-template-container').height(available_height);
            $('.portal-container').height(available_height);
            search_row = Math.max($('.search-row:eq(0)').outerHeight(), 50);
            page_row = Math.max($('.page-row:eq(0)').outerHeight(), 33);
            header = 0; //Math.max($('#completed_jobs_table thead').height(), 41);
            height = Math.floor(available_height) - header - page_row - search_row ;
            if (docw < 765 && docw >= 493) {
                row_height = 27;
            }
            else if (docw < 493) {
                row_height = 47;
            }
            else if (docw < 865) {
                row_height = 87;
            }
            else if (docw < 925) {
                row_height = 67;
            }
            else if (docw < 1415) {
                row_height = 47;
            }
            else {
                row_height = 44;
            }
            max_rows = Math.floor(height / row_height);
            if (max_rows < 5){
                box_height = header+page_row + search_row + 40 + (5 * row_height);
                if (docw < 1140) {
                    box_height += 40;
                }
                // $('.portal-job-template-container').height(box_height);
                max_rows = 5;
            }
            return max_rows;
        };

        $scope.submitJob = function (id) {
            PlaybookRun({ scope: $scope, id: id });
        };

        $scope.refresh = function () {
            $scope.$emit('LoadPortal');
        };

        $scope.refresh();

    }

PortalController.$inject = ['$scope', '$compile', '$routeParams', '$rootScope', '$location', '$log','Wait', 'ClearScope', 'Stream', 'Rest', 'GetBasePath', 'ProcessErrors',
    'PortalJobsWidget', 'generateList' , 'PortalJobTemplateList', 'SearchInit', 'PaginateInit', 'PlaybookRun'
];
