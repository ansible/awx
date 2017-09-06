/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['addPermissionsTeamsList', 'addPermissionsUsersList', 'TemplateList', 'ProjectList',
    'InventoryList', 'CredentialList', '$compile', 'generateList',
    'OrganizationList', '$window',
    function(addPermissionsTeamsList, addPermissionsUsersList, TemplateList, ProjectList,
    InventoryList, CredentialList, $compile, generateList,
    OrganizationList, $window) {
    return {
        restrict: 'E',
        scope: {
            allSelected: '=',
            view: '@',
            dataset: '='
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
            list.multiSelect = true;
            list.multiSelectExtended = true;
            list.listTitleBadge = false;
            delete list.actions;
            delete list.fieldActions;

            switch(scope.view){

                case 'Projects':
                    list.fields = {
                        name: list.fields.name,
                        scm_type: list.fields.scm_type
                    };
                    list.fields.name.ngClick = 'linkoutResource("project", project)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.scm_type.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;

                case 'Inventories':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization
                    };
                    list.fields.name.ngClick = 'linkoutResource("inventory", inventory)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.organization.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    delete list.disableRow;
                    break;

                case 'JobTemplates':
                    list.name = 'job_templates';
                    list.iterator = 'job_template';
                    list.basePath = 'job_templates';
                    list.fields = {
                        name: list.fields.name
                    };
                    list.fields.name.ngClick = 'linkoutResource("job_template", job_template)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    break;

                case 'WorkflowTemplates':
                    list.name = 'workflow_templates';
                    list.iterator = 'workflow_template';
                    list.basePath = 'workflow_job_templates';
                    list.fields = {
                        name: list.fields.name
                    };
                    list.fields.name.ngClick = 'linkoutResource("workflow_job_template", workflow_template)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    break;
                case 'Users':
                    list.fields = {
                        username: list.fields.username,
                        first_name: list.fields.first_name,
                        last_name: list.fields.last_name
                    };
                    list.fields.username.ngClick = 'linkoutResource("user", user)';
                    list.fields.username.columnClass = 'col-md-5 col-sm-5 col-xs-11';
                    list.fields.first_name.columnClass = 'col-md-3 col-sm-3 hidden-xs';
                    list.fields.last_name.columnClass = 'col-md-3 col-sm-3 hidden-xs';
                    break;
                case 'Teams':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization,
                    };
                    list.fields.name.ngClick = 'linkoutResource("team", team)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.organization.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;
                case 'Organizations':
                    list.fields = {
                        name: list.fields.name
                    };
                    list.fields.name.ngClick = 'linkoutResource("organization", organization)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    break;
                case 'Credentials':
                    list.fields = {
                        name: list.fields.name
                    };
                    list.fields.name.ngClick = 'linkoutResource("credential", credential)';
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    break;
                default:
                    list.fields = {
                        name: list.fields.name,
                        description: list.fields.description
                    };
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.description.columnClass = 'col-md-5 col-sm-5 hidden-xs';
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
            scope[`${list.name}`] = scope[`${list.iterator}_dataset`].results;

            scope.$watch(`allSelected.${list.name}`, function(){
                _.forEach(scope[`${list.name}`], isSelected);
            }, true);

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
            }

            function isSelected(item){
                item.isSelected = false;
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
