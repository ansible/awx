import ListController from './list-templates.controller';
const listTemplate = require('~features/templates/list.view.html');
import { N_ } from '../../src/i18n';

export default {
    name: 'templates',
    route: '/templates',
    ncyBreadcrumb: {
        // TODO: this would be best done with our
        // strings file pattern, but it's not possible to
        // get a handle on this route within a DI based
        // on the state tree generation as present in
        // src/templates currently
        label: N_("TEMPLATES")
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'template',
        socket: {
            "groups": {
                "jobs": ["status_changed"]
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
            controller: ListController,
            templateUrl: listTemplate,
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
                    .finally(() => Wait('stop'))
            }
        ],
    }
};
