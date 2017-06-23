import { N_ } from '../../../../../../i18n';
import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';

export default {
    name: 'inventories.edit.inventory_sources.edit.schedules.add',
    url: '/add',
    ncyBreadcrumb: {
        label: N_("CREATE SCHEDULE")
    },
    views: {
        'form': {
            controller: 'schedulerAddController',
            templateUrl: templateUrl("scheduler/schedulerForm")
        }
    }
};
