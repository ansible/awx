import jobsListController from '../../jobs/jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');

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
            ($stateParams, Wait, GetBasePath, qs) => {
                const searchParam = $stateParams.job_search;

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
