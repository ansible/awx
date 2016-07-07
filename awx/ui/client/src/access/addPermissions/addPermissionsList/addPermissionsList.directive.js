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

                        scope.search(list.iterator);
                    });
                }
            };
        }
    ];
