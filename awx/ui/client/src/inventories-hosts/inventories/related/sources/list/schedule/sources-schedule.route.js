import { N_ } from '../../../../../../i18n';

export default {
    name: 'inventories.edit.inventory_sources.edit.schedules',
    url: '/schedules',
    searchPrefix: 'schedule',
    ncyBreadcrumb: {
        label: N_('SCHEDULES')
    },
    resolve: {
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath', 'inventorySourceData',
            function(list, qs, $stateParams, GetBasePath, inventorySourceData) {
                let path = `${inventorySourceData.related.schedules}`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['inventorySourceData', function(inventorySourceData) {
            return inventorySourceData;
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
        ScheduleList: ['SchedulesList', 'inventorySourceData',
            (SchedulesList, inventorySourceData) => {
                let list = _.cloneDeep(SchedulesList);
                list.basePath = `${inventorySourceData.related.schedules}`;
                return list;
            }
        ]
    },
    views: {
        // clear form template when views render in this substate
        'form': {
            templateProvider: () => ''
        },
        // target the un-named ui-view @ root level
        '@': {
            templateProvider: function(ScheduleList, generateList, ParentObject, $filter) {
                // include name of parent resource in listTitle
                ScheduleList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                let html = generateList.build({
                    list: ScheduleList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return "<div class='InventoryManage-container'>" + generateList.insertFormView() + html + "</div>";
            },
            controller: 'schedulerListController'
        }
    }
};
