import { N_ } from '../../../src/i18n';
import jobsListController from '../jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');

export default {
    url: '/completed_jobs',
    name: 'templates.editWorkflowJobTemplate.completed_jobs',
    params: {
        job_search: {
            value: {
                page_size: '20',
                workflow_job__workflow_job_template: '',
                order_by: '-id'
            },
            dynamic: true,
            squash: ''
        }
    },
    data: {
        socket: {
            groups: {
                jobs: ['status_changed']
            }
        }
    },
    ncyBreadcrumb: {
        label: N_('COMPLETED JOBS')
    },
    views: {
        related: {
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
                const templateId = $stateParams.workflow_job_template_id;

                const searchParam = _.assign($stateParams
                    .job_search, { workflow_job__workflow_job_template: templateId });

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
