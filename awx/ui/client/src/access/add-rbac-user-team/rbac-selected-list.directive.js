/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['$compile', 'i18n', 'generateList',
    'ProjectList', 'TemplateList', 'InventoryList', 'CredentialList',
    'OrganizationList', '$window',
    function($compile, i18n, generateList,
    ProjectList, TemplateList, InventoryList, CredentialList,
    OrganizationList, $window) {
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

                delete list.actions;
                delete list.layoutClass;

                list.listTitleBadge = false;

                switch(scope.resourceType){
                    case 'projects':
                        list.fields = {
                            name: list.fields.name,
                            scm_type: list.fields.scm_type
                        };
                        delete list.staticColumns;
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = "#/projects/{{project.id}}";
                        list.fields.name.columnClass = 'col-sm-5';
                        list.fields.scm_type.columnClass = 'col-sm-5';
                        break;
                    case 'inventories':
                        list.fields = {
                            name: list.fields.name,
                            organization: list.fields.organization
                        };
                        delete list.staticColumns;
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = '{{inventory.linkToDetails}}';
                        list.fields.name.columnClass = 'col-sm-5';
                        list.fields.organization.columnClass = 'col-sm-5';
                        break;
                    case 'job_templates':
                        list.name = 'job_templates';
                        list.iterator = 'job_template';
                        list.fields = {
                            name: list.fields.name
                        };
                        list.fields.name.columnClass = 'col-sm-10';
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = "#/templates/job_template/{{job_template.id}}";
                        break;
                    case 'workflow_templates':
                        list.name = 'workflow_job_templates';
                        list.iterator = 'workflow_job_template';
                        list.fields = {
                            name: list.fields.name
                        };
                        list.fields.name.columnClass = 'col-sm-10';
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = "#/templates/workflow_job_template/{{workflow_template.id}}";
                        break;
                    case 'credentials':
                        list.fields = {
                            name: list.fields.name
                        };
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = "#/credentials/{{credential.id}}";
                        list.fields.name.columnClass = 'col-sm-10';
                        break;
                    case 'organizations':
                        list.fields = {
                            name: list.fields.name
                        };
                        delete list.fields.name.ngClick;
                        list.fields.name.ngHref = "#/organizations/{{organization.id}}";
                        list.fields.name.columnClass = 'col-sm-10';
                        break;
                }

                list.fieldActions = {
                    columnClass: 'col-sm-2',
                    remove: {
                        ngClick: `removeSelection(${list.iterator}, resourceType)`,
                        iconClass: 'fa fa-times-circle',
                        awToolTip: i18n._(`Remove ${list.iterator.replace(/_/g, ' ')}`),
                        label: i18n._('Remove'),
                        class: 'btn-sm'
                    }
                };

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

                scope.$watch(list.name, function(){
                    if(scope.list.name === 'inventories') {
                        if (scope[list.name] !== undefined) {
                            scope[list.name].forEach(function(item, item_idx) {
                                var itm = scope[list.name][item_idx];

                                if(itm.kind && itm.kind === "smart") {
                                    itm.linkToDetails = `#/inventories/smart/${itm.id}`;
                                }
                                else {
                                    itm.linkToDetails = `#/inventories/inventory/${itm.id}`;
                                }

                            });
                        }
                    }
                });

                scope.removeSelection = function(resource, type){
                    let multiselect_scope, deselectedIdx;

                    delete scope.collection[resource.id];
                    delete scope.selected[type][resource.id];

                    $('.tooltip').each(function() {
                        $(this).remove();
                    });

                    // a quick & dirty hack
                    // section 1 and section 2 elements produce sibling scopes
                    // This means events propogated from section 2 are not received in section 1
                    // The following code directly accesses the right scope by list table id
                    multiselect_scope = angular.element('#AddPermissions-body').find(`#${type}_table`).scope();
                    deselectedIdx = _.findIndex(multiselect_scope[type], {id: resource.id});
                    multiselect_scope[type][deselectedIdx].isSelected = false;
                };

                scope.linkoutResource = function(type, resource) {

                    let url;

                    switch(type){
                        case 'project':
                            url = "/#/projects/" + resource.id;
                            break;
                        case 'inventory':
                            url = resource.kind && resource.kind === "smart" ? "/#/inventories/smart/" + resource.id : "/#/inventories/inventory/" + resource.id;
                            break;
                        case 'job_template':
                            url = "/#/templates/job_template/" + resource.id;
                            break;
                        case 'workflow_job_template':
                            url = "/#/templates/workflow_job_template/" + resource.id;
                            break;
                        case 'user':
                            url = "/#/users/" + resource.id;
                            break;
                        case 'team':
                            url = "/#/teams/" + resource.id;
                            break;
                        case 'organization':
                            url = "/#/organizations/" + resource.id;
                            break;
                        case 'credential':
                            url = "/#/credentials/" + resource.id;
                            break;
                    }

                    $window.open(url,'_blank');
                };

                element.append(list_html);
                $compile(element.contents())(scope);
            }
        };
    }
];
