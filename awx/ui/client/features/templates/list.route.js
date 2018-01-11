import ListController from './list-templates.controller';
const listTemplate = require('~features/templates/list.view.html');
import { N_ } from '../../src/i18n';

function TemplatesResolve (UnifiedJobTemplate) {
    return new UnifiedJobTemplate(['get', 'options']);
}

TemplatesResolve.$inject = [
    'UnifiedJobTemplateModel'
];

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
            value: {
                type: 'workflow_job_template,job_template'
            },
            dynamic: true
        }
    },
    searchPrefix: 'template',
    views: {
        '@': {
            controller: ListController,
            templateUrl: listTemplate,
            controllerAs: 'vm'
        }
    },
    resolve: {
        resolvedModels: TemplatesResolve,
        Dataset: ['TemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
