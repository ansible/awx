import listContainerController from '~src/instance-groups/jobs/instanceGroupsJobsListContainer.controller';
import { N_ } from '../../../src/i18n';
import jobsListController from '../jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');
const listContainerTemplate = require('~src/instance-groups/jobs/instanceGroupsJobsListContainer.partial.html');

const instanceGroupJobsRoute = {
    name: 'instanceGroups.jobs',
    url: '/:instance_group_id/jobs',
    ncyBreadcrumb: {
        parent: 'instanceGroups.edit',
        label: N_('JOBS')
    },
    params: {
        job_search: {
            value: {
                page_size: '10',
                order_by: '-finished'
            },
            dynamic: true
        }
    },
    views: {
        'instanceGroupsJobsContainer@instanceGroups': {
            templateUrl: listContainerTemplate,
            controller: listContainerController,
            controllerAs: 'vm'
        },
        'jobsList@instanceGroups.jobs': {
            templateUrl: jobsListTemplate,
            controller: jobsListController,
            controllerAs: 'vm'
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
                const groupId = $stateParams.instance_group_id;

                const searchParam = $stateParams.job_search;

                const searchPath = `api/v2/instance_groups/${groupId}/jobs`;

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
        SearchBasePath: [
            '$stateParams',
            ($stateParams) => `api/v2/instance_groups/${$stateParams.instance_group_id}/jobs`
        ],
    }
};

const containerGroupJobsRoute = {
    name: 'instanceGroups.containerGroupJobs',
    url: '/container_groups/:instance_group_id/jobs',
    ncyBreadcrumb: {
        parent: 'instanceGroups.editContainerGroup',
        label: N_('JOBS')
    },
    params: {
        job_search: {
            value: {
                page_size: '10',
                order_by: '-finished'
            },
            dynamic: true
        }
    },
    views: {
        'containerGroupJobs@instanceGroups': {
            templateUrl: listContainerTemplate,
            controller: listContainerController,
            controllerAs: 'vm'
        },
        'jobsList@instanceGroups.containerGroupJobs': {
            templateUrl: jobsListTemplate,
            controller: jobsListController,
            controllerAs: 'vm'
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
            'QuerySet',
            ($stateParams, Wait, qs) => {
                const groupId = $stateParams.instance_group_id;

                const searchParam = $stateParams.job_search;

                const searchPath = `api/v2/instance_groups/${groupId}/jobs`;

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
        SearchBasePath: [
            '$stateParams',
            ($stateParams) => `api/v2/instance_groups/${$stateParams.instance_group_id}/jobs`
        ],
    }
};

export { instanceGroupJobsRoute, containerGroupJobsRoute };
