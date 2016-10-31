/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default ['addPermissionsTeamsList', 'addPermissionsUsersList', '$compile', 'generateList', 'GetBasePath', 'SelectionInit', function(addPermissionsTeamsList,
    addPermissionsUsersList, $compile, generateList,
    GetBasePath, SelectionInit) {
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

            listMap = {Teams: addPermissionsTeamsList, Users: addPermissionsUsersList};
            list = listMap[scope.view];
            list_html = generateList.build({
                mode: 'edit',
                list: list
            });

            scope.list = listMap[scope.view];
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
