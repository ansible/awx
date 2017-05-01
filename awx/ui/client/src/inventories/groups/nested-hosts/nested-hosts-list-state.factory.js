/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/
import NestedHostsListController from './nested-hosts-list.controller';
export default ['NestedHostsListDefinition', '$stateExtender', 'templateUrl', '$injector',
    function(NestedHostsListDefinition, $stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                searchPrefix: `${list.iterator}`,
                squash: '',
                name: `${formStateDefinition.name}.nested_hosts`,
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
                    // 'related@inventories.edit.groups.edit': {
                    'related': {
                        templateProvider: function(NestedHostsListDefinition, generateList) {
                            let list = _.cloneDeep(NestedHostsListDefinition);

                            let html = generateList.build({
                                list: list,
                                mode: 'edit'
                            });
                            // Include the custom group delete modal template
                            // return $templateRequest(templateUrl('inventories/groups/list/groups-list')).then((template) => {
                            //     return html.concat(template);
                            // });
                            return html;
                        },
                            controller: NestedHostsListController
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
                            path = `api/v2/groups/${$stateParams.group_id}/all_hosts`;
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
                        return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
                    }]
                }
            };

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
