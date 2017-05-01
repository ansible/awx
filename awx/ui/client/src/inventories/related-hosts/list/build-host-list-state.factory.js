/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/
import RelatedHostListController from './host-list.controller';
export default ['RelatedHostsListDefinition', '$stateExtender', 'templateUrl', '$injector',
    function(RelatedHostsListDefinition, $stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition) {
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
                        templateProvider: function(RelatedHostsListDefinition, generateList, $stateParams, GetBasePath) {
                            let list = _.cloneDeep(RelatedHostsListDefinition);
                            if($stateParams && $stateParams.group) {
                                list.basePath = GetBasePath('groups') + _.last($stateParams.group) + '/all_hosts';
                            }
                            else {
                                //reaches here if the user is on the root level group
                                list.basePath = GetBasePath('inventory') + $stateParams.inventory_id + '/hosts';
                            }
                            let html = generateList.build({
                                list: list,
                                mode: 'edit'
                            });
                            return html;
                        },
                        controller: RelatedHostListController
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
                    hostsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
                        return $stateParams.group && $stateParams.group.length > 0 ?
                            // nested context - provide all hosts managed by nodes
                            InventoryManageService.childHostsUrl(_.last($stateParams.group)) :
                            // root context - provide all hosts in an inventory
                            InventoryManageService.rootHostsUrl($stateParams.inventory_id);
                    }],
                    hostsDataset: ['RelatedHostsListDefinition', 'QuerySet', '$stateParams', 'hostsUrl', (list, qs, $stateParams, hostsUrl) => {
                        let path = hostsUrl;
                        return qs.search(path, $stateParams[`${list.iterator}_search`]);
                    }],
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
