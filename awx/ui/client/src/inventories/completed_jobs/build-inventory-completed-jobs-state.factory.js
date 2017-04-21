/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/
import JobsListController from '../../jobs/jobs-list.controller';
export default ['InventoryCompletedJobsList', '$stateExtender', 'templateUrl', '$injector',
    function(InventoryCompletedJobsList, $stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                // searchPrefix: `${list.iterator}`,
                name: `${formStateDefinition.name}.${list.iterator}s`,
                url: `/${list.iterator}s`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                params: {
                    completed_job_search: {
                        value: {
                            or__job__inventory: '',
                            or__adhoccommand__inventory: '',
                            or__inventoryupdate__inventory_source__inventory: ''
                        },
                        squash: ''
                    }
                },
                views: {
                    'related': {
                        templateProvider: function(FormDefinition, GenerateForm) {
                            let html = GenerateForm.buildCollection({
                                mode: 'edit',
                                related: `${list.iterator}s`,
                                form: typeof(FormDefinition) === 'function' ?
                                    FormDefinition() : FormDefinition
                            });
                            return html;
                        },
                        controller: JobsListController
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

                            $stateParams[`${list.iterator}_search`].or__job__inventory = $stateParams.inventory_id;
                            $stateParams[`${list.iterator}_search`].or__adhoccommand__inventory = $stateParams.inventory_id;
                            $stateParams[`${list.iterator}_search`].or__inventoryupdate__inventory_source__inventory = $stateParams.inventory_id;

                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ]
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
