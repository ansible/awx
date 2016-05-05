/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobTemplatesController($scope, $rootScope,  GetBasePath, GenerateList, PortalJobTemplateList, SearchInit, PaginateInit, PlaybookRun){


        var list = PortalJobTemplateList,
        view= GenerateList,
        defaultUrl = GetBasePath('job_templates'),
        pageSize = 12;

        $scope.submitJob = function (id) {
            PlaybookRun({ scope: $scope, id: id });
        };

        var init = function(){
            view.inject( list, {
                id : 'portal-job-templates',
                mode: 'edit',
                scope: $scope,
                searchSize: 'col-md-10 col-xs-12'
            });

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
                pageSize: pageSize
            });

            $scope.search(list.iterator);
        };
        init();
    }

PortalModeJobTemplatesController.$inject = ['$scope', '$rootScope', 'GetBasePath', 'generateList', 'PortalJobTemplateList', 'SearchInit', 'PaginateInit', 'PlaybookRun'
];
