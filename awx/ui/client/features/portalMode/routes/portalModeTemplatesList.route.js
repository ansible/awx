import { N_ } from '../../../src/i18n';
import templatesListController from '../../templates/templatesList.controller';
import indexController from '../index.controller';

const templatesListTemplate = require('~features/templates/templatesList.view.html');
const indexTemplate = require('~features/portalMode/index.view.html');

export default {
    name: 'portalMode',
    url: '/portal',
    reloadOnSearch: true,
    ncyBreadcrumb: {
        label: N_('MY VIEW')
    },
    data: {
        socket: {
            groups: {
                jobs: ['status_changed']
            }
        }
    },
    params: {
        template_search: {
            dynamic: true,
            value: {
                type: 'workflow_job_template,job_template',
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
        'templates@portalMode': {
            templateUrl: templatesListTemplate,
            controller: templatesListController,
            controllerAs: 'vm'
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
