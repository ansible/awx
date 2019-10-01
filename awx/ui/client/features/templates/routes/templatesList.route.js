import { N_ } from '../../../src/i18n';
import templatesListController from '../templatesList.controller';
import indexController from '../index.controller';

const indexTemplate = require('~features/templates/index.view.html');
const templatesListTemplate = require('~features/templates/templatesList.view.html');

export default {
    name: 'templates',
    route: '/templates',
    ncyBreadcrumb: {
        label: N_("TEMPLATES")
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'template'
    },
    params: {
        template_search: {
            dynamic: true,
            value: {
                type: 'workflow_job_template,job_template',
                order_by: 'name',
                page_size: '20'
            },
        }
    },
    searchPrefix: 'template',
    views: {
        '@': {
            templateUrl: indexTemplate,
            controller: indexController,
            controllerAs: 'vm'
        },
        'templatesList@templates': {
            controller: templatesListController,
            templateUrl: templatesListTemplate,
            controllerAs: 'vm',
        }
    },
    resolve: {
        resolvedModels: [
            'JobTemplateModel',
            'WorkflowJobTemplateModel',
            (JobTemplate, WorkflowJobTemplate) => {
                const models = [
                    new JobTemplate(['options']),
                    new WorkflowJobTemplate(['options']),
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
                const searchParam = $stateParams.template_search;
                const searchPath = GetBasePath('unified_job_templates');

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
    }
};
