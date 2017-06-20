import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';

export default {
    name: 'inventories.edit.inventory_sources.edit.schedules.edit',
    url: '/:schedule_id',
    ncyBreadcrumb: {
        label: "{{schedule_obj.name}}"
    },
    views: {
        'form': {
            templateUrl: templateUrl("scheduler/schedulerForm"),
            controller: 'schedulerEditController',
        }
    }
};
