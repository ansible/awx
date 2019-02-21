import { N_ } from '../../../src/i18n';
import jobsListController from '../jobsList.controller';

const jobsListTemplate = require('~features/jobs/jobsList.view.html');

export default {
    url: '/completed_jobs',
    params: {
        job_search: {
            value: {
                page_size: '20',
                or__job__inventory: '',
                or__adhoccommand__inventory: '',
                or__inventoryupdate__inventory_source__inventory: '',
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
        label: N_('JOBS')
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
                const inventoryId = $stateParams.inventory_id ?
                    $stateParams.inventory_id : $stateParams.smartinventory_id;

                const searchParam = _.assign($stateParams.job_search, {
                    or__job__inventory: inventoryId,
                    or__adhoccommand__inventory: inventoryId,
                    or__inventoryupdate__inventory_source__inventory: inventoryId,
                    or__workflowjob__inventory: inventoryId,
                });

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
