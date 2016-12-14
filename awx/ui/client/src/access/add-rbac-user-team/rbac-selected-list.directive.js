/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['$compile','templateUrl', 'i18n', 'generateList', 
    'ProjectList', 'TemplateList', 'InventoryList', 'CredentialList',
    function($compile, templateUrl, i18n, generateList,
    ProjectList, TemplateList, InventoryList, CredentialList) {
        return {
            restrict: 'E',
            scope: {
                resourceType: "=",
                collection: "=",
                selected: "="
            },
            link: function(scope, element, attrs) {
                console.log(scope.resourceType)
                let listMap, list, list_html;

                listMap = {
                    projects: ProjectList,
                    job_templates: TemplateList,
                    workflow_templates: TemplateList,
                    inventories: InventoryList,
                    credentials: CredentialList
                };

                list = _.cloneDeep(listMap[scope.resourceType])

                list.fieldActions = {
                    remove: {
                        ngClick: `removeSelection(${list.iterator}, resourceType)`,
                        icon: 'fa-remove',
                        awToolTip: i18n._(`Remove ${list.iterator}`),
                        label: i18n._('Remove'),
                        class: 'btn-sm'
                    }
                };
                delete list.actions;

                list.listTitleBadge = false;

                switch(scope.resourceType){

                    case 'projects':
                        list.fields = {
                            name: list.fields.name,
                            scm_type: list.fields.scm_type
                        };
                        break;

                    case 'inventories':
                        list.fields = {
                            name: list.fields.name,
                            organization: list.fields.organization
                        };
                        break;

                    case 'job_templates':
                        list.name = 'job_templates';
                        list.iterator = 'job_template';
                        list.fields = {
                            name: list.fields.name,
                            description: list.fields.description
                        };
                        break;

                    case 'workflow_templates':
                        list.name = 'workflow_templates';
                        list.iterator = 'workflow_template',
                        list.basePath = 'workflow_job_templates';
                        list.fields = {
                            name: list.fields.name,
                            description: list.fields.description
                        };
                        break;

                    default:
                        list.fields = {
                            name: list.fields.name,
                            description: list.fields.description
                        };
                }

                list.fields = _.each(list.fields, (field) => field.nosort = true);

                list_html = generateList.build({
                    mode: 'edit',
                    list: list,
                    related: false,
                    title: false,
                    showSearch: false,
                    paginate: false
                });

                scope.list = list;
                scope[`${list.iterator}_dataset`] = scope.collection;
                scope[list.name] = scope.collection;

                element.append(list_html);
                $compile(element.contents())(scope);
            }
        };
    }
];
