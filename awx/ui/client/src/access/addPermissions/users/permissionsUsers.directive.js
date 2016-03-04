/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    ['addPermissionsUsersList', 'generateList', 'GetBasePath', 'SelectionInit', 'SearchInit',
        'PaginateInit', function(addPermissionsUsersList, generateList,
            GetBasePath, SelectionInit, SearchInit, PaginateInit) {
            return {
                restrict: 'E',
                scope: {
                },
                template: "<div id='addPermissionsUsersList'></div>",
                link: function(scope, element, attrs, ctrl) {
                    scope.$on("linkLists", function() {
                        var generator = generateList,
                            list = addPermissionsUsersList,
                            url = GetBasePath("users") + "?is_superuser=false",
                            set = "users",
                            id = "addPermissionsUsersList",
                            mode = "edit";

                        scope.$watch("selectedItems", function() {
                            scope.$emit("itemsSelected", scope.selectedItems);
                        });

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
