import { N_ } from '../../../../i18n';

export default {
    url: "/completed_jobs",
    params: {
        completed_job_search: {
            value: {
                page_size: '20',
                or__job__inventory:"",
                or__adhoccommand__inventory:"",
                or__inventoryupdate__inventory_source__inventory:"",
                order_by: "-id"
            },
            dynamic: true,
            squash:""
        }
    },
    ncyBreadcrumb: {
        label: N_("COMPLETED JOBS")
    },
    views: {
        'related': {
            templateProvider: function(FormDefinition, GenerateForm) {
                let html = GenerateForm.buildCollection({
                    mode: 'edit',
                    related: 'completed_jobs',
                    form: typeof(FormDefinition) === 'function' ?
                        FormDefinition() : FormDefinition
                });
                return html;
            },
            controller: 'JobsList'
        }
    },
    resolve: {
        ListDefinition: ['InventoryCompletedJobsList', (InventoryCompletedJobsList) => {
            return InventoryCompletedJobsList;
        }],
        Dataset: ['InventoryCompletedJobsList', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                let path, interpolator;
                if (GetBasePath(list.basePath)) {
                    path = GetBasePath(list.basePath);
                } else {
                    interpolator = $interpolate(list.basePath);
                    path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                }

                let inventory_id = $stateParams.inventory_id ? $stateParams.inventory_id : $stateParams.smartinventory_id;

                $stateParams[`${list.iterator}_search`].or__job__inventory = inventory_id;
                $stateParams[`${list.iterator}_search`].or__adhoccommand__inventory = inventory_id;
                $stateParams[`${list.iterator}_search`].or__inventoryupdate__inventory_source__inventory = inventory_id;

                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
