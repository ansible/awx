import { N_ } from '../i18n';
const listTemplate = require('~features/templates/list.view.html');

export default {
    url: "/templates",
    name: 'projects.edit.templates',
    params: {
        template_search: {
            value: {
                page_size: '20',
                project: '',
                order_by: "-id"
            }
        }
    },
    ncyBreadcrumb: {
        label: N_("JOB TEMPLATES")
    },
    views: {
        'related': {
            controller: 'ProjectTemplatesListController',
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
        ListDefinition: ['TemplateList', '$transition$', (TemplateList, $transition$) => {
            let id = $transition$.params().project_id;
            TemplateList.actions.add.ngClick = `$state.go('templates.addJobTemplate', {project_id: ${id}})`;
            TemplateList.basePath = 'job_templates';
            return TemplateList;
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                let path, interpolator;
                if (GetBasePath(list.basePath)) {
                    path = GetBasePath(list.basePath);
                } else {
                    interpolator = $interpolate(list.basePath);
                    path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                }
                let project_id = $stateParams.project_id;
                $stateParams[`${list.iterator}_search`].project = project_id;
                path = GetBasePath('job_templates');
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
