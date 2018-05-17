import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';
import editScheduleResolve from '../../../../../../scheduler/editSchedule.resolve';

export default {
    name: 'inventories.edit.inventory_sources.edit.schedules.edit',
    url: '/:schedule_id',
    ncyBreadcrumb: {
        parent: 'inventories.edit.inventory_sources.edit.schedules',
        label: "{{breadcrumb.schedule_name}}"
    },
    views: {
        'scheduler@inventories': {
            templateUrl: templateUrl("scheduler/schedulerForm"),
            controller: 'schedulerEditController',
        }
    },
    resolve: editScheduleResolve()
};
