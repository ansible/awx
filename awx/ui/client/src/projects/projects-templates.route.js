import { N_ } from '../i18n';

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
        // TODO: this controller was removed and replaced
        // with the new features/templates controller
        // this view should be updated with the new
        // expanded list
        'related': {
            templateProvider: function(FormDefinition, GenerateForm) {
                let html = GenerateForm.buildCollection({
                    mode: 'edit',
                    related: 'templates',
                    form: typeof(FormDefinition) === 'function' ?
                        FormDefinition() : FormDefinition
                });
                return html;
            },
            controller: 'TemplatesListController'
        }
    },
    resolve: {
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
