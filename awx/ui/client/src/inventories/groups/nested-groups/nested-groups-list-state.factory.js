/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/
import NestedGroupsListController from './nested-groups-list.controller';
export default ['$stateExtender', 'templateUrl', '$injector',
    function($stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                searchPrefix: `${list.iterator}`,
                squash: '',
                name: `${formStateDefinition.name}.nested_groups`,
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
                        templateProvider: function(NestedGroupListDefinition, generateList) {
                            let list = _.cloneDeep(NestedGroupListDefinition);

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
                            controller: NestedGroupsListController
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
                            if($stateParams.group_id){
                                path = `api/v2/groups/${$stateParams.group_id}/children`;
                            }
                            else if($stateParams.host_id){
                                path = GetBasePath('hosts') + $stateParams.host_id + '/all_groups';
                            }
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
                        if($stateParams.host_id){
                            return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                                return res.data.results[0];
                            });
                        }
                    }],
                    inventoryData: ['InventoryManageService', '$stateParams', 'host', function(InventoryManageService, $stateParams, host) {
                        var id = ($stateParams.inventory_id) ? $stateParams.inventory_id : host.summary_fields.inventory.id;
                        return InventoryManageService.getInventory(id).then(res => res.data);
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
