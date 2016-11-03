/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'templates',
    route: '/templates',
    ncyBreadcrumb: {
        label: "TEMPLATES"
    },
    params: {
        unified_job_templates_search: {
            value: {
                type: 'workflow_job_template,job_template'
            }
        }
    },
    searchPrefix: 'unified_job_templates',
    views: {
        '@': {
            controller: 'JobTemplatesListController',
            templateProvider: function(JobTemplateList, generateList) {
                let html = generateList.build({
                    list: JobTemplateList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return generateList.insertFormView() + html;
            }
        }
    },
    resolve: {
        Dataset: ['JobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
