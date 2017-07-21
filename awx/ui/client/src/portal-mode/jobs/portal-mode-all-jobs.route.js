import { PortalModeJobsController } from '../portal-mode-jobs.controller';

// Using multiple named views requires a parent layout
// https://github.com/angular-ui/ui-router/wiki/Multiple-Named-Views
export default {
    name: 'portalMode.allJobs',
    url: '/alljobs?{job_search:queryset}',
    ncyBreadcrumb: {
        skip: true
    },
    params: {
        job_search: {
            value: {
                page_size: '20',
                order_by: '-finished'
            },
            dynamic: true
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
                    return qs.search(path, $stateParams[`${list.iterator}_search`]);
                });
            }
        ]
    }
};
