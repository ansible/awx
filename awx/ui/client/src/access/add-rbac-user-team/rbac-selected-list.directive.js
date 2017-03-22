/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['$compile', 'i18n', 'generateList',
    'ProjectList', 'TemplateList', 'InventoryList', 'CredentialList',
    'OrganizationList',
    function($compile, i18n, generateList,
    ProjectList, TemplateList, InventoryList, CredentialList,
    OrganizationList) {
        return {
            restrict: 'E',
            scope: {
                resourceType: "=",
                collection: "=",
                selected: "="
            },
            link: function(scope, element, attrs) {
                let listMap, list, list_html;

                listMap = {
                    projects: ProjectList,
                    job_templates: TemplateList,
                    workflow_templates: TemplateList,
                    inventories: InventoryList,
                    credentials: CredentialList,
                    organizations: OrganizationList
                };

                list = _.cloneDeep(listMap[scope.resourceType]);

                list.fieldActions = {
                    remove: {
                        ngClick: `removeSelection(${list.iterator}, resourceType)`,
                        iconClass: 'fa fa-times-circle',
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
                        list.fields.name.columnClass = 'col-md-5 col-sm-5 col-xs-10';
                        list.fields.scm_type.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                        break;

                    case 'inventories':
                        list.fields = {
                            name: list.fields.name,
                            organization: list.fields.organization
                        };
                        list.fields.name.columnClass = 'col-md-5 col-sm-5 col-xs-10';
                        list.fields.organization.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                        break;

                    case 'job_templates':
                    case 'workflow_templates':
                    case 'credentials':
                    case 'organizations':
                        list.name = 'job_templates';
                        list.iterator = 'job_template';
                        list.fields = {
                            name: list.fields.name,
                            description: list.fields.description
                        };
                        list.fields.name.columnClass = 'col-md-5 col-sm-5 col-xs-10';
                        list.fields.description.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                        break;
                }

                list.fields = _.each(list.fields, (field) => field.nosort = true);

                list_html = generateList.build({
                    mode: 'edit',
                    list: list,
                    related: false,
                    title: false,
                    showSearch: false,
                    showEmptyPanel: false,
                    paginate: false
                });

                scope.list = list;

                scope.$watchCollection('collection', function(selected){
                    scope[`${list.iterator}_dataset`] = scope.collection;
                    scope[list.name] = _.values(scope.collection);
                });

                scope.removeSelection = function(resource, type){
                    let multiselect_scope, deselectedIdx;

                    delete scope.collection[resource.id];
                    delete scope.selected[type][resource.id];

                    // a quick & dirty hack
                    // section 1 and section 2 elements produce sibling scopes
                    // This means events propogated from section 2 are not received in section 1
                    // The following code directly accesses the right scope by list table id
                    multiselect_scope = angular.element('#AddPermissions-body').find(`#${type}_table`).scope();
                    deselectedIdx = _.findIndex(multiselect_scope[type], {id: resource.id});
                    multiselect_scope[type][deselectedIdx].isSelected = false;
                };

                element.append(list_html);
                $compile(element.contents())(scope);
            }
        };
    }
];
