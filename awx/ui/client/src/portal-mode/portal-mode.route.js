import { templateUrl } from '../shared/template-url/template-url.factory';
import { PortalModeJobTemplatesController } from './portal-mode-job-templates.controller';
import { PortalModeJobsController } from './portal-mode-jobs.controller';

// Using multiple named views requires a parent layout
// https://github.com/angular-ui/ui-router/wiki/Multiple-Named-Views
export default {
    name: 'portalMode',
    url: '/portal?{group_search:queryset}{host_search:queryset}',
    ncyBreadcrumb: {
        label: 'MY VIEW'
    },
    params: {
        job_search: {
            value: {
                page_size: '20',
                order_by: '-finished'
            }
        },
        job_template_search: {
            value: {
                page_size: '20',
                order_by: 'name'
            }
        }
    },
    data: {
        socket: {
            "groups": {
                "jobs": ["status_changed"]
            }
        }
    },
    views: {
        'list@': {
            templateUrl: templateUrl('portal-mode/portal-mode-layout'),
            controller: ['$scope', '$rootScope', '$state', '$stateParams', 'GetBasePath', 'QuerySet', 'jobsDataset',
                function($scope, $rootScope, $state, $stateParams, GetBasePath, qs, Dataset) {
                    let path;
                    init();

                    function init() {
                        $scope.activeFilter = parseInt($stateParams.job_search.created_by) === $rootScope.current_user.id ? 'user' : 'all';
                    }

                    $scope.filterUser = function() {
                        $scope.activeFilter = 'user';
                        path = GetBasePath('jobs');
                        $stateParams.job_search.created_by = $rootScope.current_user.id;
                        qs.search(path, $stateParams.job_search);
                    };

                    $scope.filterAll = function() {
                        $scope.activeFilter = 'all';
                        delete $stateParams.job_search.created_by;
                        path = GetBasePath('jobs');
                        qs.search(path, $stateParams.job_search);
                    };
                }
            ]
        },
        // named ui-views inside the above
        'job-templates@portalMode': {
            templateProvider: function(PortalJobTemplateList, generateList) {
                let html = generateList.build({
                    list: PortalJobTemplateList,
                    mode: 'edit'
                });
                return html;
            },
            controller: PortalModeJobTemplatesController
        },
        'jobs@portalMode': {
            templateProvider: function(PortalJobsList, generateList) {
                let html = generateList.build({
                    list: PortalJobsList,
                    mode: 'edit'
                });
                return html;
            },
            controller: PortalModeJobsController
        }
    },
    resolve: {
        jobsDataset: ['PortalJobsList', 'QuerySet', '$rootScope', '$stateParams', 'GetBasePath',
            function(list, qs, $rootScope, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return $rootScope.loginConfig.promise.then(() => {
                    $stateParams[`${list.iterator}_search`].created_by = $rootScope.current_user.id;
                    return qs.search(path, $stateParams[`${list.iterator}_search`]);
                });
            }
        ],
        job_templatesDataset: ['PortalJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
