import listContainerController from '~src/instance-groups/jobs/instanceJobsListContainer.controller';
import { N_ } from '../../../src/i18n';
import jobsListController from '../jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');
const listContainerTemplate = require('~src/instance-groups/jobs/instanceJobsListContainer.partial.html');

export default {
    name: 'instanceGroups.instanceJobs',
    url: '/:instance_group_id/instances/:instance_id/jobs',
    ncyBreadcrumb: {
        parent: 'instanceGroups.instances',
        label: N_('JOBS')
    },
    views: {
        'instanceJobsContainer@instanceGroups': {
            templateUrl: listContainerTemplate,
            controller: listContainerController,
            controllerAs: 'vm'
        },
        'jobsList@instanceGroups.instanceJobs': {
            templateUrl: jobsListTemplate,
            controller: jobsListController,
            controllerAs: 'vm'
        },
    },
    params: {
        job_search: {
            value: {
                page_size: '10',
                order_by: '-finished'
            },
            dynamic: true
        },
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
                const instanceId = $stateParams.instance_id;

                const searchParam = $stateParams.job_search;

                const searchPath = `api/v2/instances/${instanceId}/jobs`;

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
        SearchBasePath: [
            '$stateParams',
            ($stateParams) => `api/v2/instances/${$stateParams.instance_id}/jobs`
        ]
    }
};
