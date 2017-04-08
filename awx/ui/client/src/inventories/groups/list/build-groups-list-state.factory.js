/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default ['InventoryGroupsList', '$stateExtender', 'templateUrl', '$injector',
    function(InventoryGroupsList, $stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition, params) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                searchPrefix: `${list.iterator}`,
                name: `${formStateDefinition.name}.${list.iterator}s`,
                url: `/${list.iterator}s`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                params: {
                    [list.iterator + '_search']: {
                        value: { order_by: field.order_by ? field.order_by : 'name' }
                    },
                },
                views: {
                    'related': {
                        templateProvider: function(InventoryGroupsList, generateList, $templateRequest, $stateParams, GetBasePath) {
                            let list = _.cloneDeep(InventoryGroupsList);
                            if($stateParams && $stateParams.group) {
                                list.basePath = GetBasePath('groups') + _.last($stateParams.group) + '/children';
                            }
                            else {
                                //reaches here if the user is on the root level group
                                list.basePath = GetBasePath('inventory') + $stateParams.inventory_id + '/root_groups';
                            }

                            let html = generateList.build({
                                list: list,
                                mode: 'edit'
                            });
                            // Include the custom group delete modal template
                            return $templateRequest(templateUrl('inventories/groups/list/groups-list')).then((template) => {
                                return html.concat(template);
                            });
                        },
                        // controller: GroupsListController
                    }
                },
                resolve: {
                    ListDefinition: () => {
                        return list;
                    },
                    Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
                        (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                            // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                            let path, interpolator;
                            if (GetBasePath(list.basePath)) {
                                path = GetBasePath(list.basePath);
                            } else {
                                interpolator = $interpolate(list.basePath);
                                path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                            }
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
                        return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
                    }]
                }
            };

            if(params.controllers && params.controllers.related && params.controllers.related[field.name]) {
                stateConfig.views.related.controller = params.controllers.related[field.name];
            }
            else if(field.name === 'permissions') {
                stateConfig.views.related.controller = 'PermissionsList';
            }
            else {
                // Generic controller
                stateConfig.views.related.controller = ['$scope', 'ListDefinition', 'Dataset',
                    function($scope, list, Dataset) {
                        $scope.list = list;
                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                        $scope[`${list.iterator}s`] = $scope[`${list.iterator}_dataset`].results;
                    }
                ];
            }

            state = $stateExtender.buildDefinition(stateConfig);
            // appy any default search parameters in form definition
            if (field.search) {
                state.params[`${field.iterator}_search`].value = _.merge(state.params[`${field.iterator}_search`].value, field.search);
            }
            return state;
        };
        return val;
    }
];
