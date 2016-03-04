/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    ['addPermissionsTeamsList', 'generateList', 'GetBasePath', 'SelectionInit', 'SearchInit',
        'PaginateInit', function(addPermissionsTeamsList, generateList,
            GetBasePath, SelectionInit, SearchInit, PaginateInit) {
            return {
                restrict: 'E',
                scope: {
                },
                template: "<div id='addPermissionsTeamsList'></div>",
                link: function(scope, element, attrs, ctrl) {
                    scope.$on("linkLists", function() {
                        var generator = generateList,
                            list = addPermissionsTeamsList,
                            url = GetBasePath("teams"),
                            set = "teams",
                            id = "addPermissionsTeamsList",
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
