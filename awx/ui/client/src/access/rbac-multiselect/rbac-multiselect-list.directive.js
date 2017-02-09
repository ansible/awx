/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['addPermissionsTeamsList', 'addPermissionsUsersList', 'TemplateList', 'ProjectList',
    'InventoryList', 'CredentialList', '$compile', 'generateList', 'GetBasePath', 'SelectionInit',
    function(addPermissionsTeamsList, addPermissionsUsersList, TemplateList, ProjectList,
    InventoryList, CredentialList, $compile, generateList, GetBasePath, SelectionInit) {
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
                Credentials: CredentialList
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
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.scm_type.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;

                case 'Inventories':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization
                    };
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.organization.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;

                case 'JobTemplates':
                    list.name = 'job_templates';
                    list.iterator = 'job_template';
                    list.basePath = 'job_templates';
                    list.fields = {
                        name: list.fields.name,
                        description: list.fields.description
                    };
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.name.ngHref = '#/templates/job_template/{{job_template.id}}';
                    list.fields.description.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;

                case 'WorkflowTemplates':
                    list.name = 'workflow_templates';
                    list.iterator = 'workflow_template';
                    list.basePath = 'workflow_job_templates';
                    list.fields = {
                        name: list.fields.name,
                        description: list.fields.description
                    };
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.name.ngHref = '#/templates/workflow_job_template/{{workflow_template.id}}';
                    list.fields.description.columnClass = 'col-md-5 col-sm-5 hidden-xs';
                    break;
                case 'Users':
                    list.fields = {
                        username: list.fields.username,
                        first_name: list.fields.first_name,
                        last_name: list.fields.last_name
                    };
                    list.fields.username.columnClass = 'col-md-5 col-sm-5 col-xs-11';
                    list.fields.first_name.columnClass = 'col-md-3 col-sm-3 hidden-xs';
                    list.fields.last_name.columnClass = 'col-md-3 col-sm-3 hidden-xs';
                    break;
                case 'Teams':
                    list.fields = {
                        name: list.fields.name,
                        organization: list.fields.organization,
                    };
                    list.fields.name.columnClass = 'col-md-6 col-sm-6 col-xs-11';
                    list.fields.organization.columnClass = 'col-md-5 col-sm-5 hidden-xs';
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
                title: false
            });

            scope.list = list;
            scope[`${list.iterator}_dataset`] = scope.dataset.data;
            scope[`${list.name}`] = scope[`${list.iterator}_dataset`].results;

            scope.$watch(list.name, function(){
                _.forEach(scope[`${list.name}`], isSelected);
            });

            function isSelected(item){
                if(_.find(scope.allSelected, {id: item.id, type: item.type})){
                    item.isSelected = true;
                }
                return item;
            }
            element.append(list_html);
            $compile(element.contents())(scope);
        }
    };
}];
