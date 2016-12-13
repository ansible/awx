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
            }
        }
    },
    searchPrefix: 'template',
    views: {
        '@': {
            controller: 'TemplatesListController',
            templateProvider: function(TemplateList, generateList) {
                let html = generateList.build({
                    list: TemplateList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return generateList.insertFormView() + html;
            }
        }
    },
    resolve: {
        Dataset: ['TemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        DataOptions: ['Rest', 'GetBasePath', '$stateParams', '$q', 'TemplateList',
            function(Rest, GetBasePath, $stateParams, $q, list) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                Rest.setUrl(path);
                var val = $q.defer();
                Rest.options()
                    .then(function(data) {
                        val.resolve(data.data.actions.GET);
                    }, function(data) {
                        val.reject(data);
                    });
                return val.promise;
            }
        ]
    }
};
