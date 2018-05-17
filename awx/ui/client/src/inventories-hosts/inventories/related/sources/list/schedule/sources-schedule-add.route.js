import { N_ } from '../../../../../../i18n';
import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';

export default {
    name: 'inventories.edit.inventory_sources.edit.schedules.add',
    url: '/add',
    ncyBreadcrumb: {
        parent: 'inventories.edit.inventory_sources.edit.schedules',
        label: N_("CREATE SCHEDULE")
    },
    views: {
        'scheduler@inventories': {
            controller: 'schedulerAddController',
            templateUrl: templateUrl("scheduler/schedulerForm")
        }
    }
};
