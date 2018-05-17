import { N_ } from '../../../src/i18n';
import jobsListController from '../jobsList.controller';

const indexTemplate = require('~features/jobs/index.view.html');
const jobsListTemplate = require('~features/jobs/jobsList.view.html');

export default {
    searchPrefix: 'job',
    name: 'jobs',
    url: '/jobs',
    ncyBreadcrumb: {
        label: N_('JOBS')
    },
    params: {
        job_search: {
            value: {
                not__launch_type: 'sync',
                order_by: '-finished'
            },
            dynamic: true,
            squash: false
        }
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'job',
        socket: {
            groups: {
                jobs: ['status_changed'],
                schedules: ['changed']
            }
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
    },
    views: {
        '@': {
            templateUrl: indexTemplate
        },
        'jobsList@jobs': {
            templateUrl: jobsListTemplate,
            controller: jobsListController,
            controllerAs: 'vm'
        }
    }
};
