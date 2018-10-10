import { N_ } from '../../../../../../i18n';

export default {
    searchPrefix: 'schedule',
    name: 'inventories.edit.inventory_sources.edit.schedules',
    url: '/schedules',
    ncyBreadcrumb: {
        parent: 'inventories.edit.inventory_sources.edit',
        label: N_('SCHEDULES')
    },
    views: {
        'related': {
            templateProvider: function(ScheduleList, generateList){
                let html = generateList.build({
                    list: ScheduleList,
                    mode: 'edit'
                });
                return html;
            },
            controller: 'schedulerListController'
        }
    },
    resolve: {
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath', 'inventorySource',
            function(list, qs, $stateParams, GetBasePath, inventorySource) {
                let path = `${inventorySource.get().related.schedules}`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['inventorySource', function(inventorySource) {
            return inventorySource.get();
        }],
        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
            function(Rest, GetBasePath, $stateParams, $q) {
                Rest.setUrl(GetBasePath('unified_jobs'));
                var val = $q.defer();
                Rest.options()
                    .then(function(data) {
                        val.resolve(data.data);
                    }, function(data) {
                        val.reject(data);
                    });
                return val.promise;
            }],
        ScheduleList: ['SchedulesList', 'inventorySource',
            (SchedulesList, inventorySource) => {
                let list = _.cloneDeep(SchedulesList);
                list.basePath = `${inventorySource.get().related.schedules}`;
                list.title = false;
                return list;
            }
        ]
    }
};
