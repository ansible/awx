/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    ['addPermissionsTeamsList', 'addPermissionsUsersList', 'generateList', 'GetBasePath', 'SelectionInit', 'SearchInit',
        'PaginateInit', function(addPermissionsTeamsList,
            addPermissionsUsersList, generateList,
            GetBasePath, SelectionInit, SearchInit, PaginateInit) {
            return {
                restrict: 'E',
                scope: {
                    allSelected: '='
                },
                template: "<div class='addPermissionsList-inner'></div>",
                link: function(scope, element, attrs, ctrl) {
                    scope.$on("linkLists", function(e) {
                        var generator = generateList,
                            list = addPermissionsTeamsList,
                            url = GetBasePath("teams"),
                            set = "teams",
                            id = "addPermissionsTeamsList",
                            mode = "edit";

                        if (attrs.type === 'users') {
                            list = addPermissionsUsersList;
                            url = GetBasePath("users") + "?is_superuser=false";
                            set = "users";
                            id = "addPermissionsUsersList";
                            mode = "edit";
                        }

                        scope.id = id;

                        scope.$watch("selectedItems", function() {
                            scope.$emit("itemsSelected", scope.selectedItems);
                        });

                        element.find(".addPermissionsList-inner")
                            .attr("id", id);

                        generator.inject(list, { id: id,
                            title: false, mode: mode, scope: scope });

                        SearchInit({ scope: scope, set: set,
                            list: list, url: url });

                        PaginateInit({ scope: scope,
                            list: list, url: url, pageSize: 5 });

                        if (scope.removePostRefresh) {
                            scope.removePostRefresh();
                        }
                        scope.removePostRefresh = scope.$on('PostRefresh', function () {
                            if(scope.allSelected && scope.allSelected.length > 0) {
                                // We need to check to see if any of the selected items are now in our list!
                                for(var i=0; i<scope.allSelected.length; i++) {
                                    for(var j=0; j<scope[set].length; j++) {
                                        if(scope.allSelected[i].id === scope[set][j].id && scope.allSelected[i].type === scope[set][j].type) {
                                            // If so, let's go ahead and mark it as selected so that select-list-item knows to check the box
                                            scope[set][j].isSelected = true;
                                        }
                                    }
                                }
                            }
                        });

                        scope.search(list.iterator);
                    });
                }
            };
        }
    ];
