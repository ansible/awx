import jobsListController from '../../jobs/jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');

export default {
    name: 'portalMode.myJobs',
    url: '/myjobs?{job_search:queryset}',
    ncyBreadcrumb: {
        skip: true
    },
    params: {
        job_search: {
            value: {
                page_size: '20',
                order_by: '-finished',
                created_by: null
            },
            dynamic: true
        }
    },
    views: {
        'jobs@portalMode': {
            templateUrl: jobsListTemplate,
            controller: jobsListController,
            controllerAs: 'vm'
        }
    },
    resolve: {
        resolvedModels: [
            'UnifiedJobModel',
            (UnifiedJob) => {
                const models = [
                    new UnifiedJob(['options']),
                ];
                return Promise.all(models);
            },
        ],
        Dataset: [
            '$stateParams',
            'Wait',
            'GetBasePath',
            'QuerySet',
            '$rootScope',
            ($stateParams, Wait, GetBasePath, qs, $rootScope) => {
                const searchParam = _.assign($stateParams.job_search, {
                    created_by: $rootScope.current_user.id });

                const searchPath = GetBasePath('unified_jobs');

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
        SearchBasePath: [
            'GetBasePath',
            (GetBasePath) => GetBasePath('unified_jobs')
        ]
    }
};
