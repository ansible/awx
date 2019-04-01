import { N_ } from '../../../src/i18n';
import templatesListController from '../templatesList.controller';

const templatesListTemplate = require('~features/templates/templatesList.view.html');

export default {
    url: "/templates",
    name: 'projects.edit.templates',
    searchPrefix: 'template',
    params: {
        template_search: {
            dynamic: true,
            value: {
                type: 'job_template',
                order_by: 'name',
                page_size: '20',
                jobtemplate__project: null
            },
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
        label: N_("JOB TEMPLATES")
    },
    views: {
        'related': {
            controller: templatesListController,
            templateUrl: templatesListTemplate,
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
                const searchPath = GetBasePath('unified_job_templates');

                const searchParam = _.assign($stateParams.template_search, {
                    jobtemplate__project: $stateParams.project_id });

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
    }
};
