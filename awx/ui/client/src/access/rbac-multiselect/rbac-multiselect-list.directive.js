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
                Templates: TemplateList,
                Inventories: InventoryList,
                Credentials: CredentialList
            };
            list = _.cloneDeep(listMap[scope.view]);
            list.multiSelect = true;
            list.multiSelectExtended = true;
            list.listTitleBadge = false;
            delete list.actions;
            delete list.fieldActions;
            
            if (scope.view !== 'Users' && scope.view !== 'Teams' && scope.view !=='Projects' && scope.view !== 'Inventories'){
                list.fields = {
                    name: list.fields.name,
                    description: list.fields.description
                };
            } else if (scope.view === 'Projects'){
                list.fields = {
                    name: list.fields.name,
                    scm_type: list.fields.scm_type
                };
            } else if (scope.view === 'Inventories'){
                list.fieds = {
                    name: list.fields.name,
                    organization: list.fields.organization
                };
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
                if(_.find(scope.allSelected, {id: item.id})){
                    item.isSelected = true;
                }
                return item;
            }
            element.append(list_html);
            $compile(element.contents())(scope);
        }
    };
}];
