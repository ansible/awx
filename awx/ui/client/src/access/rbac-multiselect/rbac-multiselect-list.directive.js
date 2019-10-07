/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['addPermissionsTeamsList', 'addPermissionsUsersList', 'TemplateList', 'ProjectList',
    'InventoryList', 'CredentialList', '$compile', 'generateList',
    'OrganizationList', '$window', 'i18n',
    function(addPermissionsTeamsList, addPermissionsUsersList, TemplateList, ProjectList,
    InventoryList, CredentialList, $compile, generateList,
    OrganizationList, $window, i18n) {
    return {
        restrict: 'E',
        scope: {
            allSelected: '=',
            view: '@',
            dataset: '=',
            defaultParams: '=?',
            objectType: '=',
            queryPrefix: '@'
        },
        template: "<div class='addPermissionsList-inner'></div>",
        link: function(scope, element, attrs, ctrl) {
            let listMap, list, list_html;

            listMap = {
                Teams: addPermissionsTeamsList,
                Users: addPermissionsUsersList,
                Projects: ProjectList,
                JobTemplates: TemplateList,
                WorkflowTemplates: TemplateList,
                Inventories: InventoryList,
                Credentials: CredentialList,
                Organizations: OrganizationList
            };
            list = _.cloneDeep(listMap[scope.view]);
            if (scope.queryPrefix) {
                list.iterator = scope.queryPrefix;
            }
            list.multiSelect = true;
            list.multiSelectExtended = true;
            list.listTitleBadge = false;
            list.layoutClass = 'List-staticColumnLayout--statusOrCheckbox';
            delete list.actions;
            delete list.fieldActions;

            switch(scope.view){

                case 'Projects':
                    list.fields = {
                        name: list.fields.name,
                        scm_type: list.fields.scm_type
                    };
                    delete list.staticColumns;
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/projects/{{project.id}}";
                    list.fields.name.columnClass = 'col-sm-6';
                    list.fields.scm_type.columnClass = 'col-sm-6';
                    break;

                case 'Inventories':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization
                    };
                    delete list.staticColumns;
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = '{{inventory.linkToDetails}}';
                    list.fields.name.columnClass = 'col-sm-6';
                    list.fields.organization.columnClass = 'col-sm-6';
                    delete list.disableRow;
                    break;

                case 'JobTemplates':
                    list.name = 'job_templates';
                    list.iterator = 'job_template';
                    list.basePath = 'job_templates';
                    list.fields = {
                        name: list.fields.name
                    };
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/templates/job_template/{{job_template.id}}";
                    list.fields.name.columnClass = 'col-sm-12';
                    break;

                case 'WorkflowTemplates':
                    list.name = 'workflow_templates';
                    list.iterator = 'workflow_template';
                    list.basePath = 'workflow_job_templates';
                    list.fields = {
                        name: list.fields.name
                    };
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/templates/workflow_job_template/{{workflow_template.id}}";
                    list.fields.name.columnClass = 'col-sm-12';
                    break;
                case 'Users':
                    if (!scope.queryPrefix) {
                        list.querySet = { order_by: 'username', page_size: '5' };
                    }
                    list.fields = {
                        username: list.fields.username,
                        first_name: list.fields.first_name,
                        last_name: list.fields.last_name
                    };
                    delete list.fields.username.ngClick;
                    list.fields.username.ngHref = "#/users/{{" + list.iterator + ".id}}";
                    list.fields.username.columnClass = 'col-sm-4 col-xs-11';
                    list.fields.first_name.columnClass = 'd-none d-sm-flex col-sm-4';
                    list.fields.last_name.columnClass = 'd-none d-sm-flex col-sm-4';
                    break;
                case 'Teams':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization,
                    };
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/teams/{{team.id}}";
                    list.fields.name.columnClass = 'col-sm-6';
                    list.fields.organization.columnClass = 'col-sm-6';
                    break;
                case 'Organizations':
                    list.fields = {
                        name: list.fields.name
                    };
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/organizations/{{organization.id}}";
                    list.fields.name.columnClass = 'col-sm-12';
                    break;
                case 'Credentials':
                    list.fields = {
                        name: list.fields.name
                    };
                    delete list.fields.name.ngClick;
                    list.fields.name.ngHref = "#/credentials/{{credential.id}}";
                    list.fields.name.columnClass = 'col-sm-12';
                    break;
                default:
                    list.fields = {
                        name: list.fields.name,
                        description: list.fields.description
                    };
                    list.fields.name.columnClass = 'col-sm-6';
                    list.fields.description.columnClass = 'col-sm-6';
            }

            list_html = generateList.build({
                mode: 'edit',
                list: list,
                related: false,
                title: false,
                hideViewPerPage: true
            });

            scope.list = list;
            scope[`${list.iterator}_dataset`] = scope.dataset.data;

            if (scope.defaultParams) {
                scope[`${list.iterator}_default_params`] = scope.defaultParams;
            }

            scope[`${list.name}`] = scope[`${list.iterator}_dataset`].results;

            scope.$watch(list.name, function(){
                _.forEach(scope[`${list.name}`], isSelected);
                optionsRequestDataProcessing();
            });

            scope.$on(`${list.iterator}_options`, function(event, data){
                scope.options = data.data.actions.GET;
                optionsRequestDataProcessing();
            });

            // iterate over the list and add fields like type label, after the
            // OPTIONS request returns, or the list is sorted/paginated/searched
            function optionsRequestDataProcessing(){
                if(scope.list.name === 'users'){
                    if (scope[list.name] !== undefined) {
                        scope[`${list.iterator}_queryset`] = list.querySet;
                        scope[list.name].forEach(function(item, item_idx) {
                            var itm = scope[list.name][item_idx];
                            if(itm.summary_fields.user_capabilities.edit){
                                // undefined doesn't render the tooltip,
                                // which is intended here.
                                itm.tooltip = undefined;
                            }
                            else if(scope.objectType === 'organization' && !itm.summary_fields.user_capabilities.edit){
                                itm.tooltip = i18n._('You do not have permission to manage this user');
                            }
                        });
                    }
                }
                if(scope.list.name === 'projects'){
                    if (scope[list.name] !== undefined) {
                        scope[list.name].forEach(function(item, item_idx) {
                            var itm = scope[list.name][item_idx];

                            // Set the item type label
                            if (list.fields.scm_type && scope.options &&
                                scope.options.hasOwnProperty('scm_type')) {
                                    scope.options.scm_type.choices.forEach(function(choice) {
                                        if (choice[0] === item.scm_type) {
                                            itm.type_label = choice[1];
                                        }
                                    });
                            }

                        });
                    }
                }
                else if(scope.list.name === 'inventories') {
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
            }

            function isSelected(item){
                _.forEach(scope.allSelected[list.name], (selectedRow) => {
                    if(selectedRow.id === item.id) {
                        item.isSelected = true;
                    }
                });
                return item;
            }

            element.append(list_html);
            $compile(element.contents())(scope);

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
        }
    };

}];
